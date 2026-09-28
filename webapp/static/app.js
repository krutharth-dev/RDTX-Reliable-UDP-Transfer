const form=document.getElementById('runForm');
const fileInput=document.getElementById('fileInput');
const timeline=document.getElementById('timeline');
const statusBadge=document.getElementById('statusBadge');
let source=null, retrans=0, drops=0;

const sliderPairs=[
 ['loss','lossValue','%'],['ackLoss','ackLossValue','%'],
 ['corruption','corruptionValue','%'],['reorder','reorderValue','%'],
 ['delay','delayValue',' ms']
];
for(const [inputId,labelId,suffix] of sliderPairs){
  const input=document.getElementById(inputId), label=document.getElementById(labelId);
  const update=()=>label.textContent=input.value+suffix; input.addEventListener('input',update); update();
}
fileInput.addEventListener('change',()=>document.getElementById('fileName').textContent=fileInput.files[0]?.name||'No file selected');
document.getElementById('clearLog').onclick=()=>timeline.innerHTML='';

function setStatus(status){
 statusBadge.textContent=status.toUpperCase(); statusBadge.className='status '+status;
}
function addEvent(event){
 if(timeline.querySelector('.empty')) timeline.innerHTML='';
 const row=document.createElement('div'); row.className='event '+event.kind;
 const t=new Date((event.timestamp||Date.now()/1000)*1000).toLocaleTimeString();
 row.innerHTML='<span class="time">'+t+'</span><span class="side">'+event.side+'</span><span class="msg"></span>';
 row.querySelector('.msg').textContent=event.message; timeline.appendChild(row); timeline.scrollTop=timeline.scrollHeight;
 if(event.kind==='drop'){drops++;document.getElementById('drops').textContent=drops}
 if(event.message?.includes('retransmission')){retrans++;document.getElementById('retransmissions').textContent=retrans}
 const m=event.message?.match(/window base (\d+)->(\d+) range=\[(\d+),(\d+)\)/);
 if(m) renderWindow(Number(m[2]),Number(m[3]),Number(m[4]));
 if(event.status) setStatus(event.status);
 if(event.status==='completed'){renderResult(event.result);loadHistory()}
}
function renderWindow(base,start,end){
 document.getElementById('windowBase').textContent=base;
 document.getElementById('windowRange').textContent='['+start+', '+end+')';
 const strip=document.getElementById('windowStrip'); strip.innerHTML='';
 const lo=Math.max(0,base-2), hi=Math.max(end+3,lo+12);
 for(let n=lo;n<hi;n++){const el=document.createElement('div');el.className='slot '+(n>=start&&n<end?'active':'');el.textContent=n;strip.appendChild(el)}
}
function renderResult(result){
 document.getElementById('resultEmpty').classList.add('hidden');document.getElementById('resultBody').classList.remove('hidden');
 document.getElementById('integrity').textContent=result.integrity;
 document.getElementById('elapsed').textContent=result.sender.elapsed.toFixed(3)+' s';
 document.getElementById('packetsSent').textContent=result.sender.datagrams_sent;
 document.getElementById('resultRetrans').textContent=result.sender.retransmissions;
 document.getElementById('resultReorder').textContent=result.sender.reordered_pairs;
 document.getElementById('throughput').textContent=result.sender.throughput_kib_s.toFixed(1)+' KiB/s';
}
async function loadHistory(){
 const rows=await fetch('/api/history').then(r=>r.json());const body=document.getElementById('historyBody');body.innerHTML='';
 for(const run of rows){const tr=document.createElement('tr');const s=run.result?.sender;
 tr.innerHTML='<td></td><td></td><td></td><td></td><td></td><td></td>';
 const cells=tr.children;cells[0].textContent=run.filename;cells[1].textContent=run.status;
 cells[2].textContent=Math.round(run.params.loss*100)+'%';cells[3].textContent=run.params.window_size;
 cells[4].textContent=s?.retransmissions??'—';cells[5].textContent=run.result?.integrity??'—';body.appendChild(tr)}
}
form.addEventListener('submit',async e=>{
 e.preventDefault();document.getElementById('formError').textContent='';retrans=0;drops=0;
 document.getElementById('retransmissions').textContent='0';document.getElementById('drops').textContent='0';timeline.innerHTML='';
 const data=new FormData(form);setStatus('running');document.getElementById('startButton').disabled=true;
 try{
  const response=await fetch('/api/runs',{method:'POST',body:data});const payload=await response.json();
  if(!response.ok) throw new Error(payload.error||'Could not start experiment');
  if(source)source.close();source=new EventSource('/api/runs/'+payload.run_id+'/events');
  source.onmessage=e=>{const event=JSON.parse(e.data);addEvent(event);if(event.status==='completed'||event.status==='failed'){source.close();document.getElementById('startButton').disabled=false}};
  source.onerror=()=>{if(source)source.close()};
 }catch(err){setStatus('failed');document.getElementById('formError').textContent=err.message;document.getElementById('startButton').disabled=false}
});
loadHistory();renderWindow(0,0,8);
