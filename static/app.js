(function(){
  var root=document.documentElement;
  // ---- Reader settings (theme / typeface / text size) ----
  var store={get:function(k){try{return localStorage.getItem(k)}catch(e){return null}},set:function(k,v){try{v==null?localStorage.removeItem(k):localStorage.setItem(k,v)}catch(e){}}};
  var btn=document.getElementById('appearance-btn'), panel=document.getElementById('appearance-panel');
  var mq=window.matchMedia?matchMedia('(prefers-color-scheme: dark)'):null;
  function metaColor(){var m=document.querySelector('meta[name=theme-color]'); if(m) m.setAttribute('content',getComputedStyle(root).getPropertyValue('--bg').trim()||'#0f1115')}
  function applyTheme(id){
    var auto=(id==='auto'||!id);
    if(auto){id=(mq&&mq.matches)?'ink':'paper'; root.setAttribute('data-theme-auto','1')} else root.removeAttribute('data-theme-auto');
    var sb=panel&&panel.querySelector('[data-theme-pick="'+id+'"]'), sc=sb?sb.getAttribute('data-scheme'):(id==='ink'?'dark':'light');
    root.setAttribute('data-theme',id); root.setAttribute('data-scheme',sc); metaColor(); sync();
  }
  function sync(){
    if(!panel) return;
    var auto=root.hasAttribute('data-theme-auto'), cur=root.getAttribute('data-theme');
    panel.querySelectorAll('[data-theme-pick]').forEach(function(b){var p=b.dataset.themePick; b.setAttribute('aria-pressed',String(auto?p==='auto':p===cur))});
    var f=document.getElementById('ap-font'); if(f) f.value=root.getAttribute('data-font')||'default';
    var z=store.get('in-size')||'100'; panel.querySelectorAll('[data-size]').forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.size===z))});
  }
  function setFont(v){ if(!v||v==='default'){root.removeAttribute('data-font');store.set('in-font',null)} else {root.setAttribute('data-font',v);store.set('in-font',v)} sync() }
  function setSize(v){ if(!v||v==='100'){root.style.fontSize='';store.set('in-size',null)} else {root.style.fontSize=v+'%';store.set('in-size',v)} sync() }
  function open(o){ if(!panel) return; panel.hidden=!o; btn.setAttribute('aria-expanded',String(o)); if(o){var c=panel.querySelector('[aria-pressed=true]')||panel.querySelector('button'); c&&c.focus()} }
  if(btn&&panel){
    btn.addEventListener('click',function(e){e.stopPropagation(); open(panel.hidden)});
    panel.addEventListener('click',function(e){
      e.stopPropagation();
      var t=e.target.closest('[data-theme-pick]'); if(t){var id=t.dataset.themePick; store.set('in-theme',id==='auto'?null:id); applyTheme(id); return}
      var z=e.target.closest('[data-size]'); if(z){setSize(z.dataset.size); return}
      if(e.target.closest('[data-ap-reset]')){store.set('in-theme',null); setFont('default'); setSize('100'); applyTheme('auto')}
    });
    var fs=document.getElementById('ap-font'); if(fs) fs.addEventListener('change',function(){setFont(fs.value)});
    document.addEventListener('click',function(){ if(!panel.hidden) open(false) });
    document.addEventListener('keydown',function(e){ if(e.key==='Escape'&&!panel.hidden){open(false); btn.focus()} });
  }
  if(mq){var onMq=function(){ if(root.hasAttribute('data-theme-auto')) applyTheme('auto') }; mq.addEventListener?mq.addEventListener('change',onMq):mq.addListener(onMq)}
  // keep tabs in sync
  window.addEventListener('storage',function(e){ if(e.key==='in-theme') applyTheme(e.newValue||'auto'); if(e.key==='in-font'){e.newValue?root.setAttribute('data-font',e.newValue):root.removeAttribute('data-font');sync()} if(e.key==='in-size'){root.style.fontSize=e.newValue?e.newValue+'%':'';sync()} });
  metaColor(); sync();
  var sel=document.getElementById('f-outlet'), seg=document.getElementById('f-side'), tseg=document.getElementById('f-topic');
  if(!sel) return;
  var cards=[].slice.call(document.querySelectorAll('main .card')), mode='', topic='', count=document.getElementById('f-count'), empty=document.getElementById('f-empty');
  var total={}; cards.forEach(function(c){total[c.dataset.id]=1}); var nTotal=Object.keys(total).length;
  function has(list,v){return (' '+(list||'')+' ').indexOf(' '+v+' ')>=0}
  function apply(){
    var o=sel.value, shown={};
    cards.forEach(function(c){
      var ok=(!o||has(c.dataset.outlets,o))&&(!topic||has(c.dataset.topics,topic))&&(!mode||(mode==='blind'&&c.dataset.blind)||(mode==='multi'&&c.querySelectorAll('.seg').length===3));
      c.classList.toggle('hidden',!ok); if(ok) shown[c.dataset.id]=1;
    });
    document.querySelectorAll('.side-list,.hero-row,.stem-strip').forEach(function(el){el.classList.toggle('hidden',!el.querySelector('.card:not(.hidden)'))});
    var n=Object.keys(shown).length;
    if(count) count.textContent=n+' of '+nTotal+' stories';
    if(empty) empty.classList.toggle('hidden',n>0);
    var u=new URL(location.href);
    o?u.searchParams.set('outlet',o):u.searchParams.delete('outlet');
    topic?u.searchParams.set('topic',topic):u.searchParams.delete('topic');
    history.replaceState(null,'',u);
  }
  function wire(group,setter){ if(!group) return; group.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;group.querySelectorAll('button').forEach(function(x){x.classList.toggle('on',x===b)});setter(b.dataset.v);apply()}); }
  var qs=new URLSearchParams(location.search), q=qs.get('outlet'), qt=qs.get('topic');
  if(q) sel.value=q;
  if(qt&&tseg){var tb=tseg.querySelector('button[data-v="'+qt+'"]'); if(tb){topic=qt;tseg.querySelectorAll('button').forEach(function(x){x.classList.toggle('on',x===tb)})}}
  sel.addEventListener('change',apply);
  wire(seg,function(v){mode=v}); wire(tseg,function(v){topic=v});
  apply();
})();
