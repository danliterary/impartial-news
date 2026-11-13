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
  var SIZES=['9','10','11','12','14','16','18','20','22','24','26','28'], SIZE_DEF='11';
  var SIZE_MIG={'90':'10','100':'11','112.5':'12','125':'14'};
  var FONT_MIG={serif:'gelasio',sans:'inter',system:'default'};
  var BUNDLED={default:1,mako:1,inter:1,newsreader:1};
  function assets(){return root.getAttribute('data-assets')||'assets/'}
  function loadSheet(id, href){
    if(document.getElementById(id)) return;
    var l=document.createElement('link'); l.id=id; l.rel='stylesheet'; l.href=href; document.head.appendChild(l);
  }
  function loadFont(id){
    if(!id||BUNDLED[id]) return;
    loadSheet('in-font-'+id, assets()+'fonts/'+id+'.css');
  }
  function loadFontPreview(){ loadSheet('in-font-preview', assets()+'fonts/preview.css') }
  function migrateFont(v){ return FONT_MIG[v]||v }
  function migrateSize(v){ return SIZE_MIG[v]||v }
  function sync(){
    if(!panel) return;
    var auto=root.hasAttribute('data-theme-auto'), cur=root.getAttribute('data-theme');
    panel.querySelectorAll('[data-theme-pick]').forEach(function(b){var p=b.dataset.themePick; b.setAttribute('aria-pressed',String(auto?p==='auto':p===cur))});
    var fid=root.getAttribute('data-font')||'default';
    panel.querySelectorAll('[data-font-pick]').forEach(function(b){b.setAttribute('aria-selected',String(b.dataset.fontPick===fid))});
    var z=root.getAttribute('data-size')||SIZE_DEF;
    var sel=document.getElementById('ap-size-select'); if(sel) sel.value=z;
    var idx=SIZES.indexOf(z);
    panel.querySelectorAll('[data-size-step]').forEach(function(b){
      var step=+b.dataset.sizeStep; b.disabled=idx<0||idx+step<0||idx+step>=SIZES.length;
    });
  }
  function setFont(v){
    v=migrateFont(v);
    if(!v||v==='default'){root.removeAttribute('data-font');store.set('in-font',null)}
    else {loadFont(v);root.setAttribute('data-font',v);store.set('in-font',v)}
    sync();
  }
  function setSize(v){
    v=migrateSize(v);
    if(!v||v===SIZE_DEF){root.removeAttribute('data-size');store.set('in-size',null)}
    else {root.setAttribute('data-size',v);store.set('in-size',v)}
    root.style.fontSize='';
    sync();
  }
  function open(o){ if(!panel) return; panel.hidden=!o; btn.setAttribute('aria-expanded',String(o)); if(o){loadFontPreview();var c=panel.querySelector('[aria-pressed=true],[aria-selected=true]')||panel.querySelector('button'); c&&c.focus()} }
  if(btn&&panel){
    btn.addEventListener('click',function(e){e.stopPropagation(); open(panel.hidden)});
    panel.addEventListener('click',function(e){
      e.stopPropagation();
      var t=e.target.closest('[data-theme-pick]'); if(t){var id=t.dataset.themePick; store.set('in-theme',id==='auto'?null:id); applyTheme(id); return}
      var fp=e.target.closest('[data-font-pick]'); if(fp){setFont(fp.dataset.fontPick); return}
      var st=e.target.closest('[data-size-step]');
      if(st){var cur=root.getAttribute('data-size')||SIZE_DEF,i=SIZES.indexOf(cur)+(+st.dataset.sizeStep); if(i>=0&&i<SIZES.length) setSize(SIZES[i]); return}
      if(e.target.closest('[data-ap-reset]')){store.set('in-theme',null); setFont('default'); setSize(SIZE_DEF); applyTheme('auto')}
    });
    var ss=document.getElementById('ap-size-select'); if(ss) ss.addEventListener('change',function(){setSize(ss.value)});
    document.addEventListener('click',function(){ if(!panel.hidden) open(false) });
    document.addEventListener('keydown',function(e){ if(e.key==='Escape'&&!panel.hidden){open(false); btn.focus()} });
  }
  if(mq){var onMq=function(){ if(root.hasAttribute('data-theme-auto')) applyTheme('auto') }; mq.addEventListener?mq.addEventListener('change',onMq):mq.addListener(onMq)}
  // keep tabs in sync
  window.addEventListener('storage',function(e){
    if(e.key==='in-theme') applyTheme(e.newValue||'auto');
    if(e.key==='in-font') setFont(e.newValue||'default');
    if(e.key==='in-size') setSize(e.newValue||SIZE_DEF);
  });
  // honour a font already applied by the head script, and migrate stale saved values
  var savedFont=migrateFont(store.get('in-font'));
  if(savedFont&&savedFont!==store.get('in-font')) store.set('in-font',savedFont==='default'?null:savedFont);
  if(root.getAttribute('data-font')) loadFont(root.getAttribute('data-font'));
  var savedSize=migrateSize(store.get('in-size'));
  if(savedSize&&savedSize!==store.get('in-size')) {store.set('in-size',savedSize===SIZE_DEF?null:savedSize); if(savedSize!==SIZE_DEF) root.setAttribute('data-size',savedSize); else root.removeAttribute('data-size')}
  root.style.fontSize='';
  metaColor(); sync();
  var preg=document.getElementById('p-region'), pside=document.getElementById('p-side');
  if(preg||pside){
    var pcards=[].slice.call(document.querySelectorAll('main .pod-card'));
    var pcount=document.getElementById('p-count'), pempty=document.getElementById('p-empty');
    var region='', side='';
    function papply(){
      var n=0;
      pcards.forEach(function(c){
        var ok=(!region||c.dataset.region===region)&&(!side||c.dataset.bucket===side);
        c.classList.toggle('hidden',!ok); if(ok) n++;
      });
      if(pcount) pcount.textContent=n+' episode'+(n===1?'':'s');
      if(pempty) pempty.classList.toggle('hidden',n>0);
    }
    function pwire(group,setter){ if(!group) return; group.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;group.querySelectorAll('button').forEach(function(x){x.classList.toggle('on',x===b)});setter(b.dataset.v);papply()}); }
    pwire(preg,function(v){region=v}); pwire(pside,function(v){side=v});
    papply();
  }
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
