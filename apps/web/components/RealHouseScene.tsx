"use client";
import { Suspense, useEffect, useMemo, useState } from "react";
import { Canvas, useThree, type ThreeEvent } from "@react-three/fiber";
import { Line, OrbitControls, useGLTF } from "@react-three/drei";
import { Box3, Matrix4, Quaternion, Raycaster, Vector3 } from "three";
import type { HouseJob, HouseLayout, Vec3 } from "@/lib/real-house";
import { packRoof, type PanelPlacement } from "@/lib/roof-layout";
import type { RoofInfo } from "@/lib/roof";

type Props = {
  job: HouseJob; layout: HouseLayout; roof: RoofInfo | null; proposedPanels: number;
  draft: Vec3[]; marking: boolean; onPoint: (p: Vec3) => void;
  onReport: (count: number, error: string | null) => void;
};
const tuple = (v: Vector3): Vec3 => [v.x,v.y,v.z];

function Building({ job, layout, roof, proposedPanels, draft, marking, onPoint, onReport }: Props) {
  const { scene: loaded } = useGLTF(job.modelUrl!, false, false);
  const scene = useMemo(() => { const s=loaded.clone(true);s.updateMatrixWorld(true);return s; },[loaded]);
  const bounds = useMemo(()=>new Box3().setFromObject(scene),[scene]);
  const center = useMemo(()=>{
    const c=bounds.getCenter(new Vector3());
    if(job.origin){
      const [lat,lng]=job.locationKey.split(",").map(Number),rad=Math.PI/180;
      c.x=(lng-job.origin.lng)*rad*6371000*Math.cos(job.origin.lat*rad);
      c.z=-(lat-job.origin.lat)*rad*6371000;
      const ray=new Raycaster(new Vector3(c.x,bounds.max.y+20,c.z),new Vector3(0,-1,0));
      const hit=ray.intersectObject(scene,true)[0];if(hit)c.y=hit.point.y;
    }
    return c;
  },[bounds,job.origin,job.locationKey,scene]);
  const size = 65;
  const camera=useThree(s=>s.camera);
  const invalidate=useThree(s=>s.invalidate);
  useEffect(()=>{camera.position.set(center.x+size*0.5,center.y+size*0.65,center.z+size*0.6);camera.lookAt(center);camera.updateProjectionMatrix();invalidate();},[camera,center,size,invalidate]);
  // ours: raycasting the mapped panels is costly; only recompute once typing in the layout inputs pauses
  const [settled,setSettled]=useState(layout);
  useEffect(()=>{const t=setTimeout(()=>setSettled(layout),300);return ()=>clearTimeout(t);},[layout]);
  const result=useMemo(()=>{
    try {
      if(settled.surfaces.length) return {panels:packRoof(settled),error:null};
      if(!(settled.width>0 && settled.height>0)) return {panels:[],error:"Enter or accept panel dimensions before placing modules."};
      if(!job.origin || !roof?.solarPanels?.length) return {panels:[],error:"No mapped panel positions are available. Mark the usable roof and exclusions."};
      if(!roof.panelWidthMeters || !roof.panelHeightMeters || Math.abs(settled.width-roof.panelWidthMeters)>0.001 || Math.abs(settled.height-roof.panelHeightMeters)>0.001)
        return {panels:[],error:"Mapped positions require the imagery provider's panel dimensions. For different equipment, mark the usable roof manually."};
      const ray = new Raycaster(), down=new Vector3(0,-1,0), panels:PanelPlacement[]=[];
      const R=6371000,rad=Math.PI/180;
      const top=bounds.max.y+20;
      const sample=(x:number,z:number)=>{
        ray.set(new Vector3(x,top,z),down);
        return ray.intersectObject(scene,true).find(hit=>hit.face && hit.face.normal.clone().transformDirection(hit.object.matrixWorld).y>0.3);
      };
      const candidates=[...roof.solarPanels].sort((a,b)=>(b.yearlyEnergyDcKwh??0)-(a.yearlyEnergyDcKwh??0)).slice(0,500);
      for(const p of candidates) {
        const seg=roof.roofSegmentStats?.[p.segmentIndex]; if(!seg) continue;
        const x=(p.center.longitude-job.origin.lng)*rad*R*Math.cos(job.origin.lat*rad),z=-(p.center.latitude-job.origin.lat)*rad*R;
        const hit=sample(x,z);if(!hit)continue;
        const az=seg.azimuthDegrees*rad,pitch=seg.pitchDegrees*rad;
        let u=new Vector3(Math.cos(az),0,Math.sin(az));
        let v=new Vector3(Math.sin(az)*Math.cos(pitch),-Math.sin(pitch),-Math.cos(az)*Math.cos(pitch));
        const normal=new Vector3().crossVectors(u,v).normalize();
        const meshNormal=hit.face!.normal.clone().transformDirection(hit.object.matrixWorld);
        if(meshNormal.dot(normal)<Math.cos(Math.PI/6)) continue;
        if(p.orientation==="LANDSCAPE") {const old=u;u=v;v=old.negate();}
        const corners=[[-1,-1],[1,-1],[1,1],[-1,1]].map(([a,b])=>hit.point.clone().addScaledVector(u,a*settled.width/2).addScaledVector(v,b*settled.height/2));
        if(corners.some(c=>{const h=sample(c.x,c.z);return !h || Math.abs(h.point.y-c.y)>0.35;}))continue;
        panels.push({position:tuple(hit.point.clone().addScaledVector(normal,0.07)),u:tuple(u),v:tuple(v),normal:tuple(normal)});
      }
      return {panels,error:panels.length?null:"Mapped panels do not align reliably with this mesh. Mark a usable roof face manually."};
    } catch(e) {return {panels:[],error:e instanceof Error?e.message:"Roof placement failed."};}
  },[scene,bounds,job.origin,settled,roof]);
  useEffect(()=>{onReport(result.panels.length,result.error);},[result,onReport]);
  const click=(e:ThreeEvent<MouseEvent>)=>{if(!marking || e.delta>3)return;e.stopPropagation();onPoint(tuple(e.point));};
  return <>
    <primitive object={scene} onClick={click} />
    {result.panels.slice(0,Math.max(0,proposedPanels)).map((p,i)=>{
      const q=new Quaternion().setFromRotationMatrix(new Matrix4().makeBasis(new Vector3(...p.u),new Vector3(...p.v),new Vector3(...p.normal)));
      return <mesh key={i} position={p.position} quaternion={q}><boxGeometry args={[layout.width,layout.height,0.035]} /><meshStandardMaterial color="#143c5c" roughness={0.6} metalness={0.25} /></mesh>;
    })}
    {layout.surfaces.flatMap((s,i)=>[<Line key={`roof-${i}`} points={[...s.outline,s.outline[0]]} color="#2563eb" lineWidth={2} />,...s.exclusions.map((p,j)=><Line key={`hole-${i}-${j}`} points={[...p,p[0]]} color="#d97706" lineWidth={3} />)])}
    {draft.length>1 && <Line points={draft} color="#2563eb" lineWidth={3} />}
    {draft.map((p,i)=><mesh key={`draft-${i}`} position={p}><sphereGeometry args={[0.13,8,8]} /><meshBasicMaterial color="#2563eb" /></mesh>)}
    <OrbitControls target={center} makeDefault enableDamping minDistance={3} maxDistance={size*3} />
  </>;
}

export default function RealHouseScene(props:Props) {
  return <Canvas frameloop="demand" camera={{position:[40,50,40],near:0.1,far:10000}} dpr={[1,1.5]} aria-label="Actual building with preliminary panel placement">
    <hemisphereLight args={["#ffffff","#ddd8c9",2]} /><directionalLight position={[30,60,20]} intensity={2} />
    <Suspense fallback={null}><Building {...props} /></Suspense>
  </Canvas>;
}
