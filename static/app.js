(function(){
  var root=document.documentElement, btn=document.querySelector('.theme-toggle');
  if(btn) btn.addEventListener('click',function(){var t=root.dataset.theme==='dark'?'light':'dark';root.dataset.theme=t;try{localStorage.setItem('in-theme',t)}catch(e){}});
  var sel=document.getElementById('f-outlet'), seg=document.getElementById('f-side');
  if(!sel) return;
  var cards=[].slice.call(document.querySelectorAll('main .card')), mode='', count=document.getElementById('f-count'), empty=document.getElementById('f-empty');
  function sides(c){var s=0;c.querySelectorAll('.seg').forEach(function(){s++});return s}
  function apply(){
    var o=sel.value, n=0;
    cards.forEach(function(c){
      var ok=(!o||(' '+c.dataset.outlets+' ').indexOf(' '+o+' ')>=0)&&(!mode||(mode==='blind'&&c.dataset.blind)||(mode==='multi'&&sides(c)===3));
      c.classList.toggle('hidden',!ok); if(ok) n++;
    });
    document.querySelectorAll('.side-list,.hero-row').forEach(function(el){el.classList.toggle('hidden',!el.querySelector('.card:not(.hidden)'))});
    if(count) count.textContent=n+' of '+cards.length+' stories';
    if(empty) empty.classList.toggle('hidden',n>0);
    var u=new URL(location.href); if(o) u.searchParams.set('outlet',o); else u.searchParams.delete('outlet'); history.replaceState(null,'',u);
  }
  var q=new URLSearchParams(location.search).get('outlet'); if(q){sel.value=q}
  sel.addEventListener('change',apply);
  if(seg) seg.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;seg.querySelectorAll('button').forEach(function(x){x.classList.toggle('on',x===b)});mode=b.dataset.v;apply()});
  apply();
})();
