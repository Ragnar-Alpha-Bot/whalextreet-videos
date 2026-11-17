"""Recursos GSAP extra para todos los vídeos (GSAP 3.15, todos los plugins son gratuitos desde GSAP 3.13).

Se cargan junto a gsap.min.js y quedan registrados; las escenas pueden usarlos con los ayudantes «wx…».
No se cargan ScrollTrigger, Observer, Inertia ni GSDevTools: son para páginas interactivas y en un vídeo no hacen nada
(GSDevTools además dibujaría su barra de control dentro del vídeo).
"""

VERSION = "3.15.0"
BASE = f"https://cdn.jsdelivr.net/npm/gsap@{VERSION}/dist/"

PLUGINS = [
    "SplitText",            # parte un texto en letras / palabras / líneas para animarlas una a una
    "ScrambleTextPlugin",   # el texto «se descifra» hasta su valor final
    "DrawSVGPlugin",        # dibuja trazos SVG como si se pintaran
    "MorphSVGPlugin",       # transforma una forma SVG en otra
    "CustomEase",           # curvas de movimiento propias
    "CustomBounce",         # rebotes con aplastamiento
    "CustomWiggle",         # temblores / vibraciones
    "EasePack",             # RoughEase, SlowMo, ExpoScaleEase
    "Flip",                 # transición suave entre dos disposiciones
    "MotionPathPlugin",     # mover objetos por una trayectoria curva
    "TextPlugin",           # escribir texto letra a letra
    "Physics2DPlugin",      # gravedad y velocidad (confeti, monedas que caen)
    "PhysicsPropsPlugin",   # física sobre cualquier propiedad
]

SCRIPTS = "".join(f'<script src="{BASE}gsap.min.js"></script>\n' if p == "gsap" else f'<script src="{BASE}{p}.min.js"></script>\n'
                  for p in ["gsap"] + PLUGINS)

# Se ejecuta antes de construir la línea de tiempo. Todo es determinista: el mismo fotograma sale igual cada vez.
PRELUDE = """gsap.registerPlugin(@@PLUGINS@@);
CustomBounce.create("wxBote",{strength:.55,squash:1.6,squashID:"wxBoteAplasta"});
CustomWiggle.create("wxTiembla",{wiggles:7,type:"easeOut"});
CustomEase.create("wxSuave","M0,0 C.16,.84 .3,1 1,1");
CustomEase.create("wxElastico","M0,0 C.3,0 .2,1.35 .55,1.12 .75,1.03 .85,1 1,1");
/* Cifras que se «descifran» hasta su valor final (el texto final ya está en el HTML). */
const wxDescifra=(sel,t,dur)=>{const e=document.querySelector(sel);if(!e)return;const fin=e.textContent;tl.to(sel,{duration:dur||.7,ease:"none",scrambleText:{text:fin,chars:"#*+=/",speed:.7,revealDelay:.15,tweenLength:false}},t);};
/* Texto que entra palabra a palabra con rotación y desenfoque suaves. */
const wxPalabras=(sel,t,dur)=>{const s=new SplitText(sel,{type:"words",wordsClass:"wx-pal"});tl.fromTo(s.words,{opacity:0,y:40,rotationX:-60,transformOrigin:"50%% 100%%"},{opacity:1,y:0,rotationX:0,duration:dur||.5,ease:"power3.out",stagger:.07},t);return s;};
/* Texto que entra letra a letra. */
const wxLetras=(sel,t,dur)=>{const s=new SplitText(sel,{type:"chars",charsClass:"wx-let"});tl.fromTo(s.chars,{opacity:0,y:30,scale:.6},{opacity:1,y:0,scale:1,duration:dur||.35,ease:"back.out(2)",stagger:.02},t);return s;};
/* Trazo que se dibuja solo (líneas, subrayados, bordes SVG). */
const wxDibuja=(sel,t,dur)=>tl.fromTo(sel,{drawSVG:"0%%"},{drawSVG:"100%%",duration:dur||.8,ease:"power2.inOut"},t);
/* Elemento que entra con un bote que se aplasta. */
const wxRebota=(sel,t,dur)=>{tl.fromTo(sel,{opacity:0,y:-160},{opacity:1,y:0,duration:dur||.9,ease:"wxBote"},t);tl.fromTo(sel,{scaleY:1,scaleX:1},{scaleY:.82,scaleX:1.12,duration:dur||.9,ease:"wxBoteAplasta",transformOrigin:"50%% 100%%",immediateRender:false},t);};
/* Sacudida corta para dar énfasis (un dato que sorprende). */
const wxSacude=(sel,t,fuerza)=>tl.fromTo(sel,{x:0},{x:fuerza||14,duration:.5,ease:"wxTiembla",immediateRender:false},t);
/* Chorro de partículas con gravedad (confeti / monedas). Posición en píxeles del vídeo. */
const wxChorro=(cont,x,y,t,color)=>{const c=document.querySelector(cont);if(!c)return;for(let i=0;i<14;i++){const p=document.createElement("i");p.style.cssText="position:absolute;left:"+x+"px;top:"+y+"px;width:14px;height:14px;border-radius:3px;background:"+(color||"var(--acc)")+";opacity:0";c.appendChild(p);tl.fromTo(p,{opacity:1,x:0,y:0},{physics2D:{velocity:380+(i%5)*90,angle:-90+(i-7)*9,gravity:900},opacity:0,duration:1.1,ease:"power1.in",immediateRender:false},t);}};
/* Objeto que sigue una trayectoria curva. */
const wxTrayecto=(sel,path,t,dur)=>tl.to(sel,{duration:dur||1.2,ease:"power1.inOut",motionPath:{path:path,autoRotate:true}},t);
/* Una forma SVG que se transforma en otra. */
const wxMorph=(sel,hacia,t,dur)=>tl.to(sel,{duration:dur||.8,ease:"power2.inOut",morphSVG:hacia},t);
/* Reorganiza elementos con una transición suave (cambia la disposición y la anima). */
const wxFlip=(sels,cambia,t,dur)=>{const st=Flip.getState(sels);cambia();tl.add(Flip.from(st,{duration:dur||.6,ease:"power2.inOut",absolute:true}),t);};
/* Texto que se escribe como a máquina. */
const wxEscribe=(sel,t,dur)=>{const e=document.querySelector(sel);if(!e)return;const fin=e.textContent;tl.to(sel,{duration:dur||1,ease:"none",text:{value:fin}},t);};
""".replace("%%", "%").replace("@@PLUGINS@@", ", ".join(PLUGINS))
