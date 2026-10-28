const {chromium}=require('/Users/nmendoza/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs');const path=require('path');
const ROOT=path.resolve(__dirname,'..');
(async()=>{const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
const report={file:path.join(ROOT,'QA-agentizada.html'),resolutions:[],errors:[],network:[],navigation:{}};
for(const [w,h] of [[1920,1080],[1280,720],[1366,768],[390,844],[360,640]]){
 const context=await browser.newContext({viewport:{width:w,height:h},reducedMotion:'reduce',offline:true});const page=await context.newPage();page.on('pageerror',e=>report.errors.push(String(e)));page.on('request',r=>{if(/^https?:/.test(r.url()))report.network.push(r.url())});
 await page.goto('file://'+path.join(ROOT,'QA-agentizada.html'));await page.evaluate(()=>document.fonts.ready);
 const result={width:w,height:h,slides:[],font:await page.evaluate(()=>({loaded:document.fonts.check('26px Saira'),family:getComputedStyle(document.querySelector('h1')).fontFamily}))};
 const folder=path.join(__dirname,`${w}x${h}`);fs.mkdirSync(folder,{recursive:true});
 for(let i=0;i<40;i++){await page.evaluate(n=>window.presentation.go(n),i);const metrics=await page.evaluate(()=>{const s=document.querySelector('.slide.active');const body=s.querySelector('.slide-body'),footer=s.querySelector('.slide-footer');const b=body.getBoundingClientRect(),f=footer.getBoundingClientRect();const items=[...body.querySelectorAll('p,h3,.callout,.row,.item,.columns,.flow,.note-sheet,.deliverables,.source-list,.source-footer,svg')];const outside=items.map(e=>({tag:e.tagName,cls:e.className?.baseVal||e.className,text:e.textContent.slice(0,70),r:e.getBoundingClientRect()})).filter(x=>x.r.bottom>f.top-5&&innerWidth>700).map(x=>({tag:x.tag,cls:x.cls,text:x.text,bottom:x.r.bottom,footer:f.top}));const overlaps=[...s.querySelectorAll('h1,.lead')].filter(e=>e.scrollHeight>e.clientHeight+2);return {title:s.querySelector('h1').textContent,bodyBottom:b.bottom,footerTop:f.top,outside,scrollWidth:s.scrollWidth,clientWidth:s.clientWidth,slideHeight:s.offsetHeight,bodyFont:parseFloat(getComputedStyle(body.querySelector('p')||s.querySelector('.lead')).fontSize),verticalScroll:document.getElementById('viewport').scrollHeight>document.getElementById('viewport').clientHeight};}); result.slides.push({n:i+1,...metrics});
 await page.screenshot({path:path.join(folder,`${String(i+1).padStart(2,'0')}.png`)});
 }
 // Button, keyboard, deep-link, index, dialog and fullscreen checks on real file://.
 await page.evaluate(()=>window.presentation.go(0));await page.keyboard.press('ArrowRight');report.navigation[`arrow-${w}`]=await page.evaluate(()=>presentation.current===1);
 await page.click('#next');report.navigation[`button-${w}`]=await page.evaluate(()=>presentation.current===2);
 await page.keyboard.press('End');report.navigation[`end-${w}`]=await page.evaluate(()=>presentation.current===39);
 await page.keyboard.press('Home');report.navigation[`home-${w}`]=await page.evaluate(()=>presentation.current===0);
 await page.click('#index');await page.click('[data-slide="38"]');report.navigation[`index-${w}`]=await page.evaluate(()=>presentation.current===38&&!document.getElementById('toc').open);
 await page.keyboard.press('?');report.navigation[`help-${w}`]=await page.locator('#helpDialog').evaluate(d=>d.open);await page.keyboard.press('Escape');report.navigation[`escape-${w}`]=await page.locator('#helpDialog').evaluate(d=>!d.open);
 await page.goto('file://'+path.join(ROOT,'QA-agentizada.html')+'#slide-33');report.navigation[`deepLink-${w}`]=await page.evaluate(()=>presentation.current===32);
 await page.evaluate(()=>presentation.go(39));await page.locator('[data-license]').click();report.navigation[`license-${w}`]=await page.locator('#licenseDialog').evaluate(d=>d.open&&d.textContent.includes('SIL OPEN FONT LICENSE'));
 result.reducedMotion=await page.evaluate(()=>getComputedStyle(document.querySelector('.halo')).animationName);
 report.resolutions.push(result);await context.close();
}
fs.writeFileSync(path.join(__dirname,'resultados.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({errors:report.errors,network:report.network,navigation:report.navigation,overflow:report.resolutions.map(r=>({size:`${r.width}x${r.height}`,font:r.font,slides:r.slides.filter(s=>s.outside.length||s.scrollWidth>s.clientWidth+2)}))},null,2));await browser.close();})();
