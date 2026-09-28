const form=document.getElementById('runForm');
const fileInput=document.getElementById('fileInput');
const timeline=document.getElementById('timeline');
const statusBadge=document.getElementById('statusBadge');
const startButton=document.getElementById('startButton');
let source=null;
let counters={retransmissions:0,drops:0,acks:0};
let currentFilter='all';
let currentRunId=null;
let runStartedAt=null;

const presets={
 baseline:{loss:0,ackLoss:0,corruption:0,reorder:0,delay:0,ackCorrupt:0,ackDelay:0,windowSize:8,timeoutMs:350},
 lossy:{loss:20,ackLoss:10,corruption:0,reorder:0,delay:0,ackCorrupt:0,ackDelay:0,windowSize:8,timeoutMs:350},
 reorder:{loss:0,ackLoss:0,corruption:0,reorder:100,delay:0,ackCorrupt:0,ackDelay:0,windowSize:8,timeoutMs:350},
 corrupt:{loss:0,ackLoss:0,corruption:10,reorder:0,delay:0,ackCorrupt:0,ackDelay:0,windowSize:8,timeoutMs:350}
};
const sliderPairs=[
 ['loss','lossValue','%'],['ackLoss','ackLossValue','%'],['corruption','corruptionValue','%'],
 ['reorder','reorderValue','%'],['delay','delayValue',' ms'],['ackCorrupt','ackCorruptValue','%'],['ackDelay','ackDelayValue',' ms']
];

function updateSliderLabels(){
 for(const [inputId,labelId,suffix] of sliderPairs){
   const input=document.getElementById(inputId),label=document.getElementById(labelId);
   label.textContent=input.value+suffix;
 }
}
for(const [inputId] of sliderPairs){document.getElementById(inputId).addEventListener('input',updateSliderLabels)}
updateSliderLabels();

function formatBytes(bytes){
 if(bytes<1024)return bytes+' B';if(bytes<1024*1024)return (bytes/1024).toFixed(1)+' KiB';
 return (bytes/(1024*1024)).toFixed(2)+' MiB';
}
fileInput.addEventListener('change',()=>{
 const file=fileInput.files[0];
 document.getElementById('fileName').textContent=file?.name||'Drop-in experiment input';
 document.getElementById('fileMeta').textContent=file?formatBytes(file.size):'Maximum 32 MiB';
});
document.getElementById('clearLog').onclick=()=>timeline.innerHTML='';
document.getElementById('resetButton').onclick=()=>applyPreset('lossy');

function applyPreset(name){
 const p=presets[name];if(!p)return;
 for(const key of ['loss','ackLoss','corruption','reorder','delay','ackCorrupt','ackDelay'])document.getElementById(key).value=p[key];
 document.getElementById('windowSize').value=p.windowSize;document.getElementById('timeoutMs').value=p.timeoutMs;
 document.querySelectorAll('.preset').forEach(b=>b.classList.toggle('active',b.dataset.preset===name));updateSliderLabels();
}
document.querySelectorAll('.preset').forEach(button=>button.addEventListener('click',()=>applyPreset(button.dataset.preset)));

function setStatus(status){
 statusBadge.textContent=status.toUpperCase();statusBadge.className='status '+status;
}
async function checkHealth(){
 try{
  const h=await fetch('/api/health').then(r=>r.json());
  document.getElementById('healthDot').classList.add('ok');
  document.getElementById('healthText').textContent='Engine online · '+h.active_runs+'/'+h.max_active_runs+' active';
 }catch(_){document.getElementById('healthText').textContent='Engine unavailable'}
}
setInterval(checkHealth,5000);checkHealth();

function resetLive(){
 counters={retransmissions:0,drops:0,acks:0};runStartedAt=Date.now();
 for(const [id,value] of [['retransmissions','0'],['drops','0'],['acks','0'],['throughput','—'],['liveElapsed','0.0 s']])document.getElementById(id).textContent=value;
 document.getElementById('resultEmpty').classList.remove('hidden');document.getElementById('resultBody').classList.add('hidden');
 timeline.innerHTML='';
}
setInterval(()=>{if(runStartedAt&&statusBadge.classList.contains('running'))document.getElementById('liveElapsed').textContent=((Date.now()-runStartedAt)/1000).toFixed(1)+' s'},200);

function addEvent(event){
 if(timeline.querySelector('.empty-state'))timeline.innerHTML='';
 if(event.kind==='drop')counters.drops++;
 if(event.kind==='retransmission')counters.retransmissions++;
 if(event.kind==='ack')counters.acks++;
 document.getElementById('drops').textContent=counters.drops;
 document.getElementById('retransmissions').textContent=counters.retransmissions;
 document.getElementById('acks').textContent=counters.acks;
 if(event.window)renderWindow(event.window.base,event.window.start,event.window.end);

 const row=document.createElement('div');row.className='event '+event.kind;row.dataset.kind=event.kind;
 if(currentFilter!=='all'&&event.kind!==currentFilter)row.classList.add('hidden-event');
 const t=new Date((event.timestamp||Date.now()/1000)*1000).toLocaleTimeString();
 row.innerHTML='<span class="time"></span><span class="side"></span><span class="msg"></span>';
 row.querySelector('.time').textContent=t;row.querySelector('.side').textContent=event.side;row.querySelector('.msg').textContent=event.message;
 timeline.appendChild(row);timeline.scrollTop=timeline.scrollHeight;
 if(event.status)setStatus(event.status);
 if(event.status==='completed'){runStartedAt=null;renderResult(event.result,currentRunId);loadHistory();checkHealth();startButton.disabled=false}
 if(event.status==='failed'){runStartedAt=null;startButton.disabled=false;loadHistory();checkHealth()}
}
function renderWindow(base,start,end){
 document.getElementById('windowBase').textContent=base;document.getElementById('windowRange').textContent='['+start+', '+end+')';
 const strip=document.getElementById('windowStrip');strip.innerHTML='';const lo=Math.max(0,base-3),hi=Math.max(end+4,lo+14);
 for(let n=lo;n<hi;n++){const el=document.createElement('div');el.className='slot '+(n>=start&&n<end?'active':n<base?'before':'');el.textContent=n;strip.appendChild(el)}
}
document.querySelectorAll('.filter').forEach(button=>button.addEventListener('click',()=>{
 currentFilter=button.dataset.kind;document.querySelectorAll('.filter').forEach(b=>b.classList.toggle('active',b===button));
 timeline.querySelectorAll('.event').forEach(row=>row.classList.toggle('hidden-event',currentFilter!=='all'&&row.dataset.kind!==currentFilter));
}));

function configText(params){
 const pct=v=>Math.round((v||0)*100)+'%';
 return [
  'window='+params.window_size,'chunk='+params.chunk_size+' B','RTO='+(params.timeout*1000).toFixed(0)+' ms',
  'DATA loss='+pct(params.loss),'ACK loss='+pct(params.ack_loss),'corruption='+pct(params.corruption),
  'reorder='+pct(params.reorder),'seed='+params.seed
 ].join(' · ');
}
function renderResult(result,runId,params=null){
 document.getElementById('resultEmpty').classList.add('hidden');document.getElementById('resultBody').classList.remove('hidden');
 document.getElementById('integrity').textContent=result.integrity;
 document.getElementById('elapsed').textContent=result.sender.elapsed.toFixed(3)+' s';
 document.getElementById('packetsSent').textContent=result.sender.datagrams_sent;
 document.getElementById('resultRetrans').textContent=result.sender.retransmissions;
 document.getElementById('resultReorder').textContent=result.sender.reordered_pairs;
 document.getElementById('ackDrops').textContent=result.receiver.simulated_ack_drops;
 document.getElementById('duplicates').textContent=result.receiver.duplicate_data_packets;
 document.getElementById('throughput').textContent=result.sender.throughput_kib_s.toFixed(1)+' KiB/s';
 document.getElementById('liveElapsed').textContent=result.sender.elapsed.toFixed(2)+' s';
 document.getElementById('downloadFile').href='/api/runs/'+runId+'/download';
 document.getElementById('exportRun').href='/api/runs/'+runId+'/export';
 if(params)document.getElementById('configSummary').textContent=configText(params);
}
async function openRun(id){
 const run=await fetch('/api/runs/'+id).then(r=>r.json());currentRunId=id;setStatus(run.status);
 if(run.result)renderResult(run.result,id,run.params);
 else{document.getElementById('resultBody').classList.add('hidden');document.getElementById('resultEmpty').classList.remove('hidden');document.getElementById('resultEmpty').textContent=run.error||'Run has not completed.'}
}

function renderBars(containerId,runs,valueFn,className=''){
 const container=document.getElementById(containerId);container.innerHTML='';
 const values=runs.map(valueFn);const max=Math.max(1,...values);
 if(!runs.length){container.innerHTML='<div class="empty-state">Complete experiments to compare them.</div>';return}
 runs.forEach((run,i)=>{
  const value=values[i];const row=document.createElement('div');row.className='bar-row';
  const label=run.params.label||run.filename;row.innerHTML='<span class="bar-label"></span><div class="bar-track"><div class="bar-fill '+className+'"></div></div><span class="bar-value"></span>';
  row.querySelector('.bar-label').textContent=label;row.querySelector('.bar-fill').style.width=Math.max(2,value/max*100)+'%';row.querySelector('.bar-value').textContent=valueFn===throughputValue?value.toFixed(0):value;
  container.appendChild(row);
 });
}
const throughputValue=run=>run.result?.sender?.throughput_kib_s||0;
const retryValue=run=>run.result?.sender?.retransmissions||0;

async function loadHistory(){
 const rows=await fetch('/api/history?limit=30').then(r=>r.json());document.getElementById('historyCount').textContent=rows.length+' runs';
 const body=document.getElementById('historyBody');body.innerHTML='';
 rows.forEach(run=>{
  const tr=document.createElement('tr');const sender=run.result?.sender;const p=run.params;
  tr.innerHTML='<td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td><button class="open-run">Open</button></td>';
  const cells=tr.children;cells[0].textContent=p.label||'—';cells[1].textContent=run.filename;
  cells[2].innerHTML='<span class="status-text '+run.status+'">'+run.status+'</span>';
  cells[3].textContent=Math.round((p.loss||0)*100)+'%';cells[4].textContent=p.window_size;
  cells[5].textContent=sender?.retransmissions??'—';cells[6].textContent=sender?sender.throughput_kib_s.toFixed(1):'—';
  cells[7].textContent=run.result?.integrity??'—';tr.querySelector('.open-run').onclick=()=>openRun(run.id);body.appendChild(tr);
 });
 const completed=rows.filter(r=>r.status==='completed'&&r.result).slice(0,8).reverse();
 renderBars('throughputBars',completed,throughputValue);renderBars('retryBars',completed,retryValue,'retry');
}

form.addEventListener('submit',async e=>{
 e.preventDefault();document.getElementById('formError').textContent='';resetLive();setStatus('running');startButton.disabled=true;
 const data=new FormData(form);
 try{
  const response=await fetch('/api/runs',{method:'POST',body:data});const payload=await response.json();
  if(!response.ok)throw new Error(payload.error||'Could not start experiment');
  currentRunId=payload.run_id;if(source)source.close();source=new EventSource('/api/runs/'+currentRunId+'/events');
  source.onmessage=e=>addEvent(JSON.parse(e.data));
  source.onerror=()=>{if(source)source.close()};
 }catch(err){runStartedAt=null;setStatus('failed');document.getElementById('formError').textContent=err.message;startButton.disabled=false;checkHealth()}
});
applyPreset('lossy');renderWindow(0,0,8);loadHistory();
