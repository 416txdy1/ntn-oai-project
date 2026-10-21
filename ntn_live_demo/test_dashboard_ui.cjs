// Isolated DOM/canvas check. Fixture values are explicitly labelled, not a live run.
const {chromium}=require('C:/Users/WSZ/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1200,height:1000}});
  const html=fs.readFileSync(path.join(__dirname,'player.html'),'utf8').replace(/<script[\s\S]*?<\/script>/g,'');
  await page.setContent(html);
  await page.addScriptTag({path:path.join(__dirname,'dashboard.js')});
  const result=await page.evaluate(()=>{
   document.querySelector('h1').textContent='界面验证 · 非实时直播';
   const monitor=new NTNDashboard.Monitor();window.testMonitor=monitor;
   monitor.history=Array.from({length:25},(_,i)=>({wall_s:70+i,iq_s:50+i*.7,cn_iq_s:50+i*.7,cn_db:19.887,ingress_kbps:352.79,fps:15,phase:'steady'}));
   const state={server_monotonic_ns:1e11,sampled_host_monotonic_ns:1e11,iq_s:77,phase:'steady',publisher_alive:true,
    spatial_mode_requested:'miso4-subarray',spatial:{observed_ports:{ue:{tx:4,rx:1},gnb:{tx:1,rx:4}},observed_workers:{ue:8,gnb:8},active_tx_ports:[0,1,2,3]},
    channels:{dl:{cn_db:3.887,delay_ms:14.927,doppler_hz:22827.6,iq_s:76.9,age_ms:100,lag_iq_s:.1,valid:true},ul:{cn_db:13.62,age_ms:100}},
    ue_ingress_kbps:74.76,ue_ingress_observed_monotonic_ns:1e11};
   window.testState=state;
   return monitor.update(state,{decoded_fps:4.42,frame_gap_ms:1200},{}).snapshot;
  });
  assert.equal(result.code,'channel_supply');
  assert.equal(await page.locator('#dlCn').textContent(),'3.89');
  assert.equal(await page.locator('#ueIngress').textContent(),'75');
  assert.match(await page.locator('#spatialMode').textContent(),/DL 4Tx×1Rx \/ UL 1Tx×4Rx/);
  assert.match(await page.locator('#spatialWorkers').textContent(),/有效发射端口 0, 1, 2, 3/);
  assert.match(await page.locator('#diagnosticTitle').textContent(),/信道劣化/);
  assert.ok(await page.locator('#channelChart').evaluate(el=>el.width>0&&el.height>0));
  await page.screenshot({path:path.join(__dirname,'dashboard-ui-test.png'),fullPage:true});
  const recovery=await page.evaluate(()=>{
   window.testState.server_monotonic_ns=102e9;window.testState.sampled_host_monotonic_ns=102e9;
   window.testState.ue_ingress_observed_monotonic_ns=102e9;window.testState.ue_ingress_kbps=500;window.testState.channels.dl.cn_db=20;
   return window.testMonitor.update(window.testState,{decoded_fps:1,frame_gap_ms:1200},{}).snapshot;
  });
  assert.equal(recovery.code,'recovery_tail');
  await page.evaluate(()=>{window.testState.server_monotonic_ns+=5e9;window.testMonitor.update(window.testState,{decoded_fps:0,frame_gap_ms:5000},{});});
  assert.equal(await page.locator('#dlCn').textContent(),'—');
  assert.match(await page.locator('#diagnosticTitle').textContent(),/过期/);
  await page.setViewportSize({width:720,height:1000});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  console.log('DOM/canvas: channel values, correlated warning, recovery, stale guard and responsive layout PASS');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
