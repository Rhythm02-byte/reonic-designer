"use client";
import dynamic from "next/dynamic";
import { Component, useCallback, useEffect, useState, type ReactNode } from "react";
import { Button, ErrorNote, Segmented } from "./ui";
import type { GeoLocation } from "./Location";
import { locationKey, type HouseAsset, type HouseJob, type HouseLayout, type Vec3 } from "@/lib/real-house";
import { fetchRoof, type RoofInfo } from "@/lib/roof";
import { surfaceFrame } from "@/lib/roof-layout";

const Scene=dynamic(()=>import("./RealHouseScene"),{ssr:false,loading:()=> <p className="p-6 text-sm">Loading the real building…</p>});
const VIEW_KEY="house-view"; // ours: per-session choice; Stylised is the fast, reliable default for the demo
const readView=():"stylised"|"real"=>{try{return sessionStorage.getItem(VIEW_KEY)==="real"?"real":"stylised";}catch{return "stylised";}};
const EMPTY:HouseLayout={surfaces:[],width:0,height:0,gap:0.02,setback:0.3};
class ModelBoundary extends Component<{children:ReactNode;fallback:ReactNode},{failed:boolean}> {
  state={failed:false};
  static getDerivedStateFromError(){return {failed:true};}
  render(){return this.state.failed?<div className="relative h-full">{this.props.fallback}<p className="absolute bottom-3 left-3 rounded-lg bg-paper p-2 text-xs text-amber-900">Real-house rendering failed. Showing the fallback.</p></div>:this.props.children;}
}

type Props={
  location:GeoLocation|null; asset?:HouseAsset; layout?:HouseLayout; proposedPanels:number; existingPv:boolean;
  fallback:ReactNode; onAsset:(asset:HouseAsset|undefined)=>void; onLayout:(layout:HouseLayout)=>void;
  onCapacity:(n:number)=>void;
};
export function RealHouse({location,asset,layout=EMPTY,proposedPanels,existingPv,fallback,onAsset,onLayout,onCapacity}:Props){
  const [job,setJob]=useState<HouseJob|null>(null),[roof,setRoof]=useState<{key:string;data:RoofInfo}|null>(null);
  const [error,setError]=useState<string|null>(null),[starting,setStarting]=useState(false),[view,setViewState]=useState<"stylised"|"real">("stylised");
  const [mark,setMark]=useState<"roof"|"exclusion"|null>(null),[draft,setDraft]=useState<Vec3[]>([]);
  const [report,setReport]=useState<{count:number;error:string|null}>({count:0,error:null}),[spaces,setSpaces]=useState("");
  const [reviewed,setReviewed]=useState(false),[gone,setGone]=useState(false),[adjustOpen,setAdjustOpen]=useState(false); // ours: gone = saved import vanished (404); adjustOpen = "Adjust roof" panel
  useEffect(()=>{setViewState(readView());},[]); // eslint-disable-line react-hooks/set-state-in-effect -- ours: sessionStorage is client-only; read after hydration
  const setView=(v:"stylised"|"real")=>{setViewState(v);try{sessionStorage.setItem(VIEW_KEY,v);}catch{/* private mode */}};
  const fallbackMode=view==="stylised";
  const key=location?locationKey(location.lat,location.lng):"";
  const latitude=location?.lat, longitude=location?.lng;
  const currentAsset=asset?.locationKey===key?asset:undefined;
  const activeJob=job?.locationKey===key?job:null;
  const id=activeJob?.id??currentAsset?.id;
  useEffect(()=>{
    if(latitude===undefined||longitude===undefined)return;let active=true;
    fetchRoof(latitude,longitude).then(data=>{if(active)setRoof({key,data});},()=>{});
    return ()=>{active=false;};
  },[latitude,longitude,key]);
  useEffect(()=>{
    if(!id)return;let active=true;
    const poll=()=>fetch(`/api/real-house/${id}`,{cache:"no-store",signal:AbortSignal.timeout(8000)}).then(async r=>{
      if(r.status===404){ // ours: asset gone; stop polling and offer a fresh import
        if(active){clearInterval(timer);setJob(null);onAsset(undefined);setGone(true);setError(null);}
        return;
      }
      const data=await r.json();if(!r.ok)throw new Error(data.error??"Import status unavailable.");
      if(active){setJob(data.job);setError(null);if(data.job.state!=="running")clearInterval(timer);}
    }).catch(e=>{if(active)setError(e.message);});
    const timer=setInterval(poll,2500);void poll();return ()=>{active=false;clearInterval(timer);};
  },[id]); // eslint-disable-line react-hooks/exhaustive-deps -- ours: onAsset only clears a stale id
  useEffect(()=>{ // ours: a finished import for this location opens as the default view; never starts an export
    if(latitude===undefined||longitude===undefined||id)return;let active=true;
    fetch(`/api/real-house?lat=${latitude}&lng=${longitude}`,{cache:"no-store",signal:AbortSignal.timeout(8000)}).then(r=>r.ok?r.json():null).then(d=>{
      if(active&&d?.job?.state==="ready"&&d.job.locationKey===key){setJob(d.job);onAsset({id:d.job.id,locationKey:key});}
    }).catch(()=>{});
    return ()=>{active=false;};
  },[latitude,longitude,key,id]); // eslint-disable-line react-hooks/exhaustive-deps -- ours: onAsset is a fresh closure each render
  const [loaded,setLoaded]=useState(false);
  const onLoaded=useCallback(()=>setLoaded(true),[]);
  const onReport=useCallback((count:number,issue:string|null)=>setReport({count,error:issue}),[]);
  async function start(){
    if(!location)return; // ours: the button itself is the building confirmation
    setStarting(true);setError(null);setGone(false);setView("real");
    try{
      const r=await fetch("/api/real-house",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...location,confirmed:true}),signal:AbortSignal.timeout(15000)});
      const d=await r.json();if(!r.ok)throw new Error(d.error??"Import failed.");
      setJob(d.job);onAsset({id:d.job.id,locationKey:key});
    }catch(e){setError(e instanceof Error?e.message:"Import failed.");}finally{setStarting(false);}
  }
  function updateLayout(next:HouseLayout){onLayout(next);setReviewed(false);setSpaces("");}
  function finish(){
    try{
      if(mark==="roof"){
        const surface={outline:draft,exclusions:[]};surfaceFrame(surface);
        updateLayout({...layout,surfaces:[...layout.surfaces,surface]});
      }else if(mark==="exclusion"){
        if(draft.length<3)throw new Error("Mark at least three exclusion corners.");
        const surface=layout.surfaces.at(-1);if(!surface)throw new Error("Mark a roof first.");
        const frame=surfaceFrame(surface),points=draft.map(p=>frame.lift(frame.project(p)));
        updateLayout({...layout,surfaces:layout.surfaces.map((s,i)=>i===layout.surfaces.length-1?{...s,exclusions:[...s.exclusions,points]}:s)});
      }
      setDraft([]);setMark(null);setError(null);
    }catch(e){setError(e instanceof Error?e.message:"Invalid roof outline.");}
  }
  const ready=activeJob?.state==="ready" && !!activeJob.modelUrl;
  const show=ready&&!fallbackMode;
  const capacity=spaces.trim()===""?(existingPv?NaN:report.count):Number(spaces);
  const canConfirm=reviewed&&Number.isInteger(capacity)&&capacity>=0&&capacity<=report.count&&report.count>0;
  const solar=roof?.key===key?roof.data:null;
  return <div>
    {location&&<div className="flex items-center justify-between gap-3 border-b border-zinc-200 px-3 py-2"><span className="text-xs text-quiet">House view</span><div className="w-56"><Segmented name="house-view" label="House view" value={view} options={[{value:"stylised",label:"Stylised"},{value:"real",label:"Real 3D"}]} onChange={v=>{setView(v);if(v==="real"&&!ready&&!starting&&activeJob?.state!=="running")void start();}}/></div></div>}
    {location&&!ready&&view==="real"&&(gone||activeJob?.state==="failed"||error)&&<div className="border-b border-zinc-200 p-3 text-xs">{/* ours: only problems show here; loading is the overlay on the house */}
      {activeJob?.state==="failed"?<p className="text-amber-900">{activeJob.error}</p>:null}
      <ErrorNote error={error}/>
    </div>}
    <div className="relative h-[320px] bg-sand sm:h-[480px]">
      {show?<>
        {!loaded&&<div className="absolute inset-0">{fallback}</div>}
        <div className={loaded?"h-full":"absolute inset-0 opacity-0"}><ModelBoundary key={activeJob.id} fallback={fallback}><Scene job={activeJob} roof={solar} layout={layout} proposedPanels={proposedPanels} draft={draft} marking={!!mark} onPoint={p=>setDraft(d=>[...d,p])} onReport={onReport} onLoaded={onLoaded}/></ModelBoundary></div>
      </>:fallback}
      {view==="real"&&!loaded&&(starting||activeJob?.state==="running"||show)&&<p role="status" className="pointer-events-none absolute top-3 right-4 rounded-lg bg-paper/90 px-2 py-1 text-xs text-quiet">Loading real building…</p>}
      <p className="pointer-events-none absolute top-3 left-4 rounded-lg bg-paper/90 px-2 py-1 text-xs text-quiet">{mark?`Click ${mark} corners; the first edge aligns the panel rows.`:"Drag to turn · scroll to zoom"}</p>
    </div>
    {/* ours: one quiet line instead of the manual roof marking (removed before the demo: too fiddly) */}
    {show&&loaded&&<div className="flex flex-wrap items-center gap-3 border-t border-zinc-200 p-3 text-xs">
      {report.error?<p className="text-amber-900">{report.error}</p>:<p className="text-quiet">Roof faces from Google Solar · fits ~{report.count} panels · {Math.min(proposedPanels,report.count)} of {proposedPanels} designed shown. Preliminary.</p>}
      <ErrorNote error={error}/>
    </div>}
  </div>;
}
