"use client";
import { Canvas } from "@react-three/fiber";
import { Bounds, Center, OrbitControls, useGLTF } from "@react-three/drei";
import { Component, Suspense, useEffect, useState, type ReactNode } from "react";
import { Button, ErrorNote } from "./ui";
import type { GeoLocation } from "./Location";
import { locationKey } from "@/lib/real-house";
import type { Lod2Job } from "@/lib/lod2-jobs";

class ModelBoundary extends Component<{children:ReactNode;fallback:ReactNode},{failed:boolean}> {
  state={failed:false};
  static getDerivedStateFromError(){return {failed:true};}
  render(){return this.state.failed?this.props.fallback:this.props.children;}
}

function Model({url}:{url:string}){
  const {scene}=useGLTF(url,false,false);
  return <Bounds fit clip observe margin={1.2}><Center><primitive object={scene}/></Center></Bounds>;
}

// LoD2 cadastre + Blender render: panels and devices are already baked into the GLB, so the viewer only displays it.
export default function Lod2House({location,fallback}:{location:GeoLocation|null;fallback:ReactNode}){
  const [job,setJob]=useState<Lod2Job|null>(null),[error,setError]=useState<string|null>(null),[starting,setStarting]=useState(false);
  const key=location?locationKey(location.lat,location.lng):"";
  const active=job?.locationKey===key?job:null;
  const id=active?.state==="running"?active.id:undefined;
  useEffect(()=>{
    if(!id)return;let live=true;
    const poll=()=>fetch(`/api/lod2-house/${id}`,{cache:"no-store",signal:AbortSignal.timeout(8000)}).then(async r=>{
      const d=await r.json();if(!r.ok)throw new Error(d.error??"Render status unavailable.");
      if(live)setJob(d.job);
    }).catch(e=>{if(live)setError(e.message);});
    const timer=setInterval(poll,2500);return ()=>{live=false;clearInterval(timer);};
  },[id]);
  async function start(){
    if(!location)return;
    setStarting(true);setError(null);
    try{
      const r=await fetch("/api/lod2-house",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(location),signal:AbortSignal.timeout(15000)});
      const d=await r.json();if(!r.ok)throw new Error(d.error??"Render failed.");
      setJob(d.job);
    }catch(e){setError(e instanceof Error?e.message:"Render failed.");}finally{setStarting(false);}
  }
  const url=active?.state==="ready"?active.modelUrl:undefined;
  return <div>
    {location&&!url&&<div className="space-y-2 border-b border-zinc-200 p-3 text-xs">
      <div className="flex flex-wrap items-center gap-2"><Button variant="secondary" disabled={starting||active?.state==="running"} onClick={start}>{starting?"Starting…":active?.state==="running"?"Building house…":"Build the LoD2 house for this pin"}</Button><span className="text-quiet">Cadastral LoD2 (Bavaria, Schleswig-Holstein) with panels and devices placed.</span></div>
      {active&&<p role="status" className="text-quiet">{active.stage}{active.state==="failed"?` · ${active.error}`:""}</p>}
      <ErrorNote error={error}/>
    </div>}
    <div className="relative h-[320px] bg-sand sm:h-[480px]">
      {url?<ModelBoundary key={url} fallback={fallback}>
        <Canvas frameloop="demand" camera={{position:[20,18,20],near:0.1,far:5000}} dpr={[1,1.5]} aria-label="LoD2 building with placed panels and devices">
          <hemisphereLight args={["#ffffff","#ddd8c9",2]}/><directionalLight position={[30,60,20]} intensity={2}/>
          <Suspense fallback={null}><Model url={url}/></Suspense>
          <OrbitControls makeDefault enableDamping/>
        </Canvas>
      </ModelBoundary>:fallback}
      {url&&<p className="pointer-events-none absolute top-3 left-4 rounded-lg bg-paper/90 px-2 py-1 text-xs text-quiet">{active?.source??"LoD2"}{active?.panels?` · ${active.panels} panels`:""} · drag to turn</p>}
    </div>
  </div>;
}
