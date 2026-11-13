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
  function open(o){ if(!panel) return; if(o&&typeof closeSync==='function') closeSync(); panel.hidden=!o; btn.setAttribute('aria-expanded',String(o)); if(o){loadFontPreview();var c=panel.querySelector('[aria-pressed=true],[aria-selected=true]')||panel.querySelector('button'); c&&c.focus()} }
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

  // ---- Sync / refresh sources ----
  var REPO='danliterary/impartial-news';
  var WORKFLOW='pages.yml';
  var API='https://api.github.com/repos/'+REPO+'/actions/workflows/'+WORKFLOW;
  var TOKEN_KEY='in-gh-token';
  var syncRoot=document.getElementById('sync-root');
  var syncBtn=document.getElementById('sync-btn');
  var syncPanel=document.getElementById('sync-panel');
  var pollTimer=null, toastTimer=null, activeRunId=null, dispatchAt=0, lastStatus=null, checking=false, waitLive=false;

  function token(){return store.get(TOKEN_KEY)||''}
  function statusUrl(){return assets()+'status.json?t='+Date.now()}
  function relTime(iso){
    if(!iso) return '';
    var t=Date.parse(iso); if(!isFinite(t)) return '';
    var s=Math.round((Date.now()-t)/1000);
    if(s<0&&s>-90) return 'just now';
    if(s<20) return 'just now';
    if(s<60) return s+' seconds ago';
    var m=Math.round(s/60);
    if(m===1) return 'a minute ago';
    if(m<60) return m+' minutes ago';
    var h=Math.round(m/60);
    if(h===1) return 'about an hour ago';
    if(h<48) return h+' hours ago';
    var d=Math.round(h/24);
    return d===1?'yesterday':d+' days ago';
  }
  function setSyncStatus(state,text){
    var dot=document.getElementById('sync-dot'), tx=document.getElementById('sync-status-text');
    if(dot) dot.setAttribute('data-state',state||'idle');
    if(tx) tx.textContent=text||'Idle';
    if(syncBtn) syncBtn.classList.toggle('busy',state==='checking'||state==='syncing');
  }
  function toast(msg,ms){
    var el=document.getElementById('sync-toast'); if(!el) return;
    el.textContent=msg||'';
    el.hidden=!msg;
    if(toastTimer) clearTimeout(toastTimer);
    if(msg) toastTimer=setTimeout(function(){el.hidden=true}, ms||4200);
  }
  function syncTokenUI(){
    var has=!!token();
    var howto=document.getElementById('sync-howto');
    var ok=document.getElementById('sync-token-ok');
    if(howto) howto.hidden=has;
    if(ok) ok.hidden=!has;
  }
  function pageBuilt(){return (syncRoot&&syncRoot.getAttribute('data-built'))||root.getAttribute('data-built')||''}
  function updateLastSynced(iso,uk){
    var t=document.getElementById('sync-built'), r=document.getElementById('sync-rel');
    if(t){
      if(iso) t.setAttribute('datetime',iso);
      if(uk) t.textContent=uk;
    }
    if(r) r.textContent=relTime((t&&t.getAttribute('datetime'))||iso||pageBuilt());
  }
  function isNewer(iso,than){
    var a=Date.parse(iso||''), b=Date.parse(than||'');
    return isFinite(a)&&isFinite(b)&&(a-b>1500);
  }
  function reloadFresh(){
    toast('New stories are in — reloading…', 8000);
    var u=new URL(location.href);
    u.searchParams.set('sync', Date.now().toString(36));
    setTimeout(function(){location.replace(u.toString())}, 450);
  }
  function ghHeaders(){
    var h={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'};
    var tok=token();
    if(tok) h.Authorization='Bearer '+tok;
    return h;
  }
  function attrNum(name, fallback){
    var v=syncRoot&&syncRoot.getAttribute(name);
    return (v||fallback||'').toString();
  }
  function feedCounts(){
    var feeds=(lastStatus&&lastStatus.feeds_total)||attrNum('data-feeds-total','121');
    var pods=(lastStatus&&(lastStatus.podcasts_total||lastStatus.podcasts_ok))||attrNum('data-podcasts-total','25');
    return {feeds:feeds,pods:pods};
  }
  function runMessage(run, jobs){
    if(!run) return 'Syncing on GitHub Actions…';
    var st=run.status, c=feedCounts();
    if(st==='queued'||st==='waiting'||st==='requested'||st==='pending') return 'Queued…';
    if(st==='in_progress'){
      if(jobs&&jobs.jobs){
        var list=jobs.jobs;
        var build=null, deploy=null, i;
        for(i=0;i<list.length;i++){
          if(/deploy/i.test(list[i].name)) deploy=list[i];
          else if(/build/i.test(list[i].name)) build=list[i];
        }
        if(deploy&&(deploy.status==='in_progress'||(build&&build.conclusion==='success'&&deploy.status!=='completed')))
          return 'Deploying…';
        if(build&&(build.status==='in_progress'||build.status==='queued'))
          return 'Fetching '+c.feeds+' feeds & '+c.pods+' podcasts…';
      }
      return 'Fetching '+c.feeds+' feeds & '+c.pods+' podcasts…';
    }
    if(st==='completed'){
      if(run.conclusion==='success') return 'Build finished — waiting for the live site…';
      if(run.conclusion==='cancelled') return 'The last sync was cancelled.';
      if(run.conclusion==='failure'||run.conclusion==='timed_out') return 'The last sync failed. You can try again or run it on GitHub.';
    }
    return 'Syncing on GitHub Actions…';
  }
  function stopPoll(){if(pollTimer){clearTimeout(pollTimer);pollTimer=null}}
  function schedulePoll(ms){stopPoll();pollTimer=setTimeout(function(){refresh(false)}, ms)}
  function pollDelay(){return token()?5000:15000}

  function latestActive(runs){
    if(!runs||!runs.length) return null;
    var i, r, found=null;
    for(i=0;i<runs.length;i++){
      r=runs[i];
      if(r.status==='queued'||r.status==='in_progress'||r.status==='waiting'||r.status==='requested'||r.status==='pending'){
        found=r; break;
      }
    }
    return found;
  }
  function latestSinceDispatch(runs){
    if(!runs||!runs.length) return null;
    if(!dispatchAt) return runs[0];
    var i, r, t, cutoff=dispatchAt-8000;
    for(i=0;i<runs.length;i++){
      r=runs[i];
      t=Date.parse(r.created_at||r.run_started_at||'');
      if(!isFinite(t)||t>=cutoff) return r;
    }
    return null;
  }

  function refresh(fromUser){
    if(checking) return Promise.resolve();
    checking=true;
    if(!waitLive&&!activeRunId) setSyncStatus('checking','Checking…');
    var statusP=fetch(statusUrl(),{cache:'no-store',credentials:'omit'}).then(function(r){
      if(!r.ok) throw new Error('status');
      return r.json();
    });
    var runsP=fetch(API+'/runs?per_page=5',{cache:'no-store',credentials:'omit',headers:ghHeaders()}).then(function(r){
      if(r.status===403||r.status===429) throw new Error('rate');
      if(!r.ok) throw new Error('runs');
      return r.json();
    }).catch(function(err){return {__err:err}});

    return Promise.all([statusP, runsP]).then(function(pair){
      checking=false;
      var st=pair[0], runsWrap=pair[1], runs=(runsWrap&&runsWrap.workflow_runs)||[];
      lastStatus=st;
      if(st&&st.generated_at) updateLastSynced(st.generated_at, st.generated_at_uk);
      else updateLastSynced();

      if(st&&isNewer(st.generated_at, pageBuilt())){
        stopPoll(); waitLive=false; activeRunId=null;
        setSyncStatus('ok','A newer build is live');
        reloadFresh();
        return;
      }

      var active=latestActive(runs);
      var ours=dispatchAt?latestSinceDispatch(runs):null;
      var focus=active||((ours&&ours.status!=='completed')?ours:null);

      if(focus){
        activeRunId=focus.id;
        waitLive=false;
        var jobsP=fetch('https://api.github.com/repos/'+REPO+'/actions/runs/'+focus.id+'/jobs',{cache:'no-store',credentials:'omit',headers:ghHeaders()}).then(function(r){return r.ok?r.json():null}).catch(function(){return null});
        return jobsP.then(function(jobs){
          setSyncStatus('syncing', runMessage(focus, jobs));
          schedulePoll(pollDelay());
        });
      }

      if(ours&&ours.status==='completed'){
        if(ours.conclusion==='success'){
          waitLive=true; activeRunId=ours.id;
          setSyncStatus('syncing','Deploying… waiting for the live site');
          schedulePoll(pollDelay());
          return;
        }
        dispatchAt=0; activeRunId=null; waitLive=false;
        setSyncStatus('error', runMessage(ours));
        if(fromUser) toast(runMessage(ours), 6000);
        return;
      }

      if(waitLive){
        if(dispatchAt&&Date.now()-dispatchAt>20*60*1000){
          waitLive=false; stopPoll();
          setSyncStatus('idle','The new build should be live shortly. Try Check for updates.');
          return;
        }
        setSyncStatus('syncing','Deploying… waiting for the live site');
        schedulePoll(pollDelay());
        return;
      }

      stopPoll();
      setSyncStatus('ok',"You're on the latest build");
    }).catch(function(err){
      checking=false;
      updateLastSynced();
      if(err&&err.message==='rate'){
        setSyncStatus('error','GitHub rate limit reached. You can still reload if a newer build is live, or run the workflow on GitHub.');
      } else if(err&&err.message==='status'){
        setSyncStatus('error','Could not read the latest build status.');
      } else {
        setSyncStatus('error','Could not reach GitHub. Try again, or run the workflow on GitHub.');
      }
    });
  }

  function dispatchSync(){
    if(!token()){
      openSync(true);
      var field=document.getElementById('sync-token');
      setSyncStatus('idle','Save a token, or run the workflow on GitHub');
      if(field) field.focus();
      toast('Save a GitHub token for one-click sync, or run the workflow on GitHub.', 6000);
      return;
    }
    if(activeRunId||waitLive){
      openSync(true);
      refresh(true);
      return;
    }
    setSyncStatus('syncing','Starting a full sync…');
    syncBtn&&syncBtn.classList.add('busy');
    fetch(API+'/dispatches',{
      method:'POST',
      credentials:'omit',
      headers:Object.assign({'Content-Type':'application/json'}, ghHeaders()),
      body:JSON.stringify({ref:'main'})
    }).then(function(r){
      if(r.status===204||r.status===200){
        dispatchAt=Date.now();
        waitLive=false;
        setSyncStatus('syncing','Queued…');
        toast('Sync started on GitHub Actions.');
        schedulePoll(2500);
        return;
      }
      if(r.status===401||r.status===403){
        setSyncStatus('error','That token was not accepted. Check it has Actions: Read and write on this repository.');
        return;
      }
      if(r.status===422){
        dispatchAt=Date.now();
        setSyncStatus('syncing','A run may already be in progress…');
        schedulePoll(2500);
        return;
      }
      setSyncStatus('error','Could not start the workflow ('+r.status+'). You can run it on GitHub instead.');
    }).catch(function(){
      setSyncStatus('error','Could not reach GitHub. Try again, or run the workflow on GitHub.');
    });
  }

  function closeSync(){
    if(!syncPanel||syncPanel.hidden) return;
    syncPanel.hidden=true;
    if(syncBtn) syncBtn.setAttribute('aria-expanded','false');
  }
  function openSync(o){
    if(!syncPanel) return;
    if(o){ if(typeof open==='function'&&panel&&!panel.hidden) open(false) }
    syncPanel.hidden=!o;
    if(syncBtn) syncBtn.setAttribute('aria-expanded',String(!!o));
    if(o){
      updateLastSynced();
      syncTokenUI();
      refresh(true);
      var c=document.getElementById('sync-check')||syncPanel.querySelector('button');
      c&&c.focus();
    }
  }

  if(syncBtn&&syncPanel){
    updateLastSynced();
    syncTokenUI();
    syncBtn.addEventListener('click',function(e){
      e.stopPropagation();
      openSync(syncPanel.hidden);
    });
    syncPanel.addEventListener('click',function(e){e.stopPropagation()});
    var checkBtn=document.getElementById('sync-check');
    if(checkBtn) checkBtn.addEventListener('click',function(){refresh(true)});
    var nowBtn=document.getElementById('sync-now');
    if(nowBtn) nowBtn.addEventListener('click',function(){dispatchSync()});
    var form=document.getElementById('sync-token-form');
    if(form) form.addEventListener('submit',function(e){
      e.preventDefault();
      var field=document.getElementById('sync-token');
      var v=field&&field.value?field.value.trim():'';
      if(!v){ if(field) field.focus(); return; }
      store.set(TOKEN_KEY,v);
      if(field) field.value='';
      syncTokenUI();
      setSyncStatus('ok','Token saved on this device');
      toast('Token saved on this device.');
    });
    var forget=document.getElementById('sync-forget');
    if(forget) forget.addEventListener('click',function(){
      store.set(TOKEN_KEY,null);
      syncTokenUI();
      setSyncStatus('idle','Token removed from this browser');
    });
  }

  document.addEventListener('click',function(){
    if(panel&&!panel.hidden) open(false);
    closeSync();
  });
  document.addEventListener('keydown',function(e){
    if(e.key!=='Escape') return;
    if(panel&&!panel.hidden){open(false);btn&&btn.focus();return}
    if(syncPanel&&!syncPanel.hidden){closeSync();syncBtn&&syncBtn.focus()}
  });
  window.addEventListener('storage',function(e){
    if(e.key===TOKEN_KEY) syncTokenUI();
  });

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
