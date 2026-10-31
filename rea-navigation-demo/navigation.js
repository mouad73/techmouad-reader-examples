/* Independent reconstruction of the tested menu/header behavior, not original source. */
(() => {
  const button=document.querySelector('[data-menu-toggle]');
  const panel=document.querySelector('[data-navigation]');
  const header=document.querySelector('[data-header]');
  let open=false;
  function showMenu(next){
    open=Boolean(next);
    button.setAttribute('aria-expanded',open?'true':'false');
    button.setAttribute('aria-label',open?'Close navigation':'Open navigation');
    panel.classList[open?'add':'remove']('is-open');
    document.body.classList[open?'add':'remove']('nav-open');
  }
  button.addEventListener('click',()=>showMenu(!open));
  for(const link of panel.querySelectorAll('a[href^="#"]'))link.addEventListener('click',()=>showMenu(false));
  window.addEventListener('resize',()=>{if(window.innerWidth>=861)showMenu(false);});
  function paintHeader(){header.classList.toggle('is-scrolled',window.scrollY>=25);}
  window.addEventListener('scroll',paintHeader,{passive:true});
  showMenu(false);paintHeader();
})();
