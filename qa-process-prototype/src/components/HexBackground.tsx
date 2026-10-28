import { useEffect, useRef } from 'react';

type Hex = { x: number; y: number; path: Path2D; energy: number; phase: number };

/** A decorative honeycomb: the static grid is painted once, only the local glow animates. */
export function HexBackground() {
  const field = useRef<HTMLDivElement>(null);
  const base = useRef<HTMLCanvasElement>(null);
  const glow = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const host = field.current, baseCanvas = base.current, glowCanvas = glow.current;
    if (!host || !baseCanvas || !glowCanvas) return;
    const baseContext = baseCanvas.getContext('2d'), glowContext = glowCanvas.getContext('2d');
    if (!baseContext || !glowContext) return;
    const motion = matchMedia('(prefers-reduced-motion: reduce)');
    const finePointer = matchMedia('(hover: hover) and (pointer: fine)');
    const radius = 33, rowHeight = Math.sqrt(3) * radius, influence = 185;
    let width = 0, height = 0, frame = 0, previousTime = 0;
    let cells: Hex[] = [];
    let pointer: { x: number; y: number } | null = null;
    let disposed = false;

    function drawGlow(time: number) {
      frame = 0;
      if (disposed || document.hidden) return;
      // Keep the breathing effect at about 30 fps instead of repainting on every mouse event.
      if (!motion.matches && previousTime && time - previousTime < 30) {
        frame = requestAnimationFrame(drawGlow);
        return;
      }
      const elapsed = Math.min(time - (previousTime || time - 33), 80);
      previousTime = time;
      const ease = motion.matches ? 1 : 1 - Math.exp(-elapsed / 170);
      glowContext!.clearRect(0, 0, width, height);
      let alive = false;
      for (const cell of cells) {
        const distance = pointer ? Math.hypot(pointer.x - cell.x, pointer.y - cell.y) : Infinity;
        const target = Math.max(0, 1 - distance / influence) ** 1.6;
        cell.energy += (target - cell.energy) * ease;
        if (cell.energy < 0.006 && target === 0) { cell.energy = 0; continue; }
        alive = true;
        const breath = motion.matches ? 0.8 : 0.73 + Math.sin(time / 680 - cell.phase) * 0.27;
        const strength = cell.energy * breath;
        glowContext!.fillStyle = `rgba(225,31,143,${strength * 0.19})`;
        glowContext!.strokeStyle = `rgba(225,31,143,${strength * 0.82})`;
        glowContext!.lineWidth = 0.85 + strength * 0.65;
        glowContext!.shadowColor = `rgba(225,31,143,${strength * 0.6})`;
        glowContext!.shadowBlur = strength * 13;
        glowContext!.fill(cell.path);
        glowContext!.stroke(cell.path);
      }
      glowContext!.shadowBlur = 0;
      // Stop completely once the pointer leaves and the last cells have faded out.
      if (alive && !motion.matches) frame = requestAnimationFrame(drawGlow);
    }
    function requestDraw() {
      if (!frame && !disposed && !document.hidden) frame = requestAnimationFrame(drawGlow);
    }
    function resize() {
      const rect = host!.getBoundingClientRect();
      width = rect.width; height = rect.height;
      const scale = Math.min(devicePixelRatio || 1, 1.75);
      for (const canvas of [baseCanvas!, glowCanvas!]) {
        canvas.width = Math.round(width * scale);
        canvas.height = Math.round(height * scale);
      }
      baseContext!.setTransform(scale, 0, 0, scale, 0, 0);
      glowContext!.setTransform(scale, 0, 0, scale, 0, 0);
      baseContext!.clearRect(0, 0, width, height);
      baseContext!.lineWidth = 0.7;
      cells = [];
      for (let column = -1; column < width / (radius * 1.5) + 1; column++) {
        for (let row = -1; row < height / rowHeight + 1; row++) {
          const x = column * radius * 1.5;
          const y = row * rowHeight + (Math.abs(column % 2) ? rowHeight / 2 : 0);
          const path = new Path2D();
          for (let corner = 0; corner < 6; corner++) {
            const angle = corner * Math.PI / 3;
            const px = x + radius * Math.cos(angle), py = y + radius * Math.sin(angle);
            if (corner === 0) path.moveTo(px, py); else path.lineTo(px, py);
          }
          path.closePath();
          const phase = (Math.sin(column * 13.7 + row * 7.9) + 1) * Math.PI;
          baseContext!.fillStyle = `rgba(0,79,86,${0.035 + (Math.sin(phase) + 1) * 0.018})`;
          baseContext!.strokeStyle = 'rgba(0,132,143,0.20)';
          baseContext!.fill(path);
          baseContext!.stroke(path);
          cells.push({ x, y, path, energy: 0, phase });
        }
      }
      requestDraw();
    }
    function move(event: PointerEvent) {
      if (event.pointerType === 'touch' || !finePointer.matches) return;
      const rect = host!.getBoundingClientRect();
      pointer = { x: event.clientX - rect.left, y: event.clientY - rect.top };
      requestDraw();
    }
    function leave() { pointer = null; requestDraw(); }
    function visibility() {
      if (document.hidden) {
        cancelAnimationFrame(frame); frame = 0; pointer = null; previousTime = 0;
        cells.forEach(cell => { cell.energy = 0; });
        glowContext!.clearRect(0, 0, width, height);
      } else requestDraw();
    }
    function preferences() {
      cancelAnimationFrame(frame); frame = 0; previousTime = 0;
      if (!finePointer.matches) pointer = null;
      requestDraw();
    }
    const observer = new ResizeObserver(resize);
    observer.observe(host);
    document.addEventListener('pointermove', move, { passive: true });
    document.documentElement.addEventListener('pointerleave', leave);
    window.addEventListener('blur', leave);
    document.addEventListener('visibilitychange', visibility);
    motion.addEventListener('change', preferences);
    finePointer.addEventListener('change', preferences);
    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      observer.disconnect();
      document.removeEventListener('pointermove', move);
      document.documentElement.removeEventListener('pointerleave', leave);
      window.removeEventListener('blur', leave);
      document.removeEventListener('visibilitychange', visibility);
      motion.removeEventListener('change', preferences);
      finePointer.removeEventListener('change', preferences);
    };
  }, []);

  return <div ref={field} className="hex-background" aria-hidden="true"><canvas ref={base} className="hex-grid"/><canvas ref={glow} className="hex-glow"/></div>;
}
