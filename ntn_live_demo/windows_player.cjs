// Native Windows audio output; receives only the already-OAI-traversed UE relay.
const {chromium}=require('C:/Users/WSZ/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path');
process.env.TEMP='C:\\Users\\WSZ\\AppData\\Local\\Temp';process.env.TMP=process.env.TEMP;
const base='C:/Users/WSZ/.codex/visualizations/2026/09/29/01a0ec57-7509-74c2-9656-23dc0cdc5f07';
const tag=process.argv[2];if(!/^live-[a-z0-9-]+$/.test(tag))throw new Error('Invalid run tag');
const output=path.join(base,'ntn-audio-runs',tag);fs.mkdirSync(output,{recursive:true});
(async()=>{
let running=true;process.on('SIGINT',()=>running=false);process.on('SIGTERM',()=>running=false);
const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:false,ignoreDefaultArgs:['--mute-audio'],
 args:['--autoplay-policy=no-user-gesture-required','--allow-loopback-in-peer-connection','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
try{
const page=await browser.newPage({viewport:{width:1200,height:1000}});
await page.goto('http://127.0.0.1:8765/',{waitUntil:'domcontentloaded',timeout:30000});
let failures=0,nextShot=Date.now()+10000,number=0;const deadline=Date.now()+1800000;
while(running&&Date.now()<deadline){
 try{const response=await fetch('http://127.0.0.1:8765/state',{signal:AbortSignal.timeout(3000)});const state=await response.json();failures=0;if(state.stop_requested)break;}catch(e){if(++failures>=3)break;}
 if(Date.now()>=nextShot){await page.screenshot({path:path.join(output,'player-'+String(++number).padStart(3,'0')+'.png')});nextShot=Date.now()+20000;}
 await page.waitForTimeout(500);
}
await page.screenshot({path:path.join(output,'player-final.png')});
}finally{await browser.close();}
console.log('WINDOWS_PLAYER_CLOSED',tag,'SHOTS',output);
})().catch(e=>{console.error(e);process.exit(1)});
