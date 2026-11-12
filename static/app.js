(function(){
  var root=document.documentElement, btn=document.querySelector('.theme-toggle');
  if(btn) btn.addEventListener('click',function(){var t=root.dataset.theme==='dark'?'light':'dark';root.dataset.theme=t;try{localStorage.setItem('in-theme',t)}catch(e){}});
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
