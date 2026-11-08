"use client";
import { Suspense, useEffect, useMemo, useState } from "react";
import { Canvas, useThree, type ThreeEvent } from "@react-three/fiber";
import { Line, OrbitControls, useGLTF } from "@react-three/drei";
import { Box3, Group, Matrix4, Mesh, MeshStandardMaterial, Quaternion, Raycaster, Vector3, type Object3D } from "three";
import type { HouseJob, HouseLayout, Vec3 } from "@/lib/real-house";
import { packRoof } from "@/lib/roof-layout";
import { buildHeightfield, MODULE, placeFromSolar, placeOnGrid, type Heightfield } from "@/lib/roof-heightfield";
import type { RoofInfo } from "@/lib/roof";

type Props = {
  job: HouseJob; layout: HouseLayout; roof: RoofInfo | null; proposedPanels: number;
  draft: Vec3[]; marking: boolean; onPoint: (p: Vec3) => void;
  onReport: (count: number, error: string | null) => void;
  onLoaded?: () => void;
};
const tuple = (v: Vector3): Vec3 => [v.x,v.y,v.z];
const STYLISED = "/models/house.glb"; // ours: Faris's Blender house; its PV_Panel_01 is the shared panel look
// ours: panel look on the photo mesh (blue glass with a slight sky reflection, light aluminium frame)
const GLASS = new MeshStandardMaterial({ color: "#27467a", roughness: 0.18, metalness: 0.55, emissive: "#16305c", emissiveIntensity: 0.35 });
const FRAME = new MeshStandardMaterial({ color: "#d4d8de", roughness: 0.4, metalness: 0.7 });
const fields = new WeakMap<Object3D, Map<string, Heightfield>>(); // ours: built once per loaded GLB, survives view toggles

/** Faris's panel (frame + cell grid), re-based so local x = width, y = height (down the slope), z = up. */
function usePanelTemplate() {
  const { scene } = useGLTF(STYLISED, false, false);
  return useMemo(() => {
    const node = scene.getObjectByName("PV_Panel_01");
    if (!node) return null;
    const inner = node.clone(true);
    // ours: on the bright photo mesh Faris's dark cells read as black blocks; dark parts become blue glass, light parts (frame) stay
    inner.traverse(o=>{
      const m=o as Mesh; if(!m.isMesh) return;
      const mat=(Array.isArray(m.material)?m.material[0]:m.material) as MeshStandardMaterial;
      const c=mat?.color; const dark=!c || (c.r+c.g+c.b)/3<0.25;
      m.material = dark ? GLASS : FRAME;
    });
    inner.position.set(0,0,0); inner.quaternion.identity(); inner.scale.set(1,1,1); inner.updateMatrixWorld(true);
    const box = new Box3().setFromObject(inner), size = box.getSize(new Vector3()), mid = box.getCenter(new Vector3());
    inner.position.copy(mid).negate();
    const axes = [new Vector3(1,0,0),new Vector3(0,1,0),new Vector3(0,0,1)], dims=[size.x,size.y,size.z];
    const order = [0,1,2].sort((a,b)=>dims[a]-dims[b]); // thin, width, length
    const t = axes[order[0]], w = axes[order[1]];
    // Blender's +Z (cells side) became glTF +Y; keep the cell side facing up
    const up = t.y !== 0 ? t : t.clone().negate();
    const h = new Vector3().crossVectors(up, w); // right-handed: w × h = up
    const rot = new Matrix4().makeBasis(w, h, up).invert();
    const pivot = new Group(); pivot.add(inner); pivot.quaternion.setFromRotationMatrix(rot);
    return { object: pivot, width: dims[order[1]], height: dims[order[2]] };
  }, [scene]);
}

function Building({ job, layout, roof, proposedPanels, draft, marking, onPoint, onReport, onLoaded }: Props) {
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
  const size = 38;
  const camera=useThree(s=>s.camera);
  const invalidate=useThree(s=>s.invalidate);
  // ours: raycasting the mapped panels is costly; only recompute once typing in the layout inputs pauses
  const [settled,setSettled]=useState(layout);
  useEffect(()=>{const t=setTimeout(()=>setSettled(layout),300);return ()=>clearTimeout(t);},[layout]);
  // ours: triangle binning near the pin, once per GLB, after the mesh is on screen (not during render)
  const fieldKey=`${center.x.toFixed(2)},${center.z.toFixed(2)}`;
  const [field,setField]=useState<Heightfield|null>(()=>fields.get(loaded)?.get(fieldKey)??null);
  useEffect(()=>{
    if(field)return;
    const t=setTimeout(()=>{
      const f=buildHeightfield(loaded,center),m=fields.get(loaded)??new Map<string,Heightfield>();
      m.set(fieldKey,f);fields.set(loaded,m);setField(f);
    },50);
    return ()=>clearTimeout(t);
  },[field,loaded,center,fieldKey]);
  const template=usePanelTemplate();
  const result=useMemo(()=>{
    if(!field)return {panels:[],width:0,height:0,error:null};
    try {
      if(settled.surfaces.length) return {panels:packRoof(settled),width:settled.width,height:settled.height,error:null};
      if(job.origin && roof?.solarPanels?.length) {
        const mapped=placeFromSolar(field,roof,job.origin);
        if(mapped.panels.length) return {...mapped,error:null};
      }
      const w=settled.width>=0.3?settled.width:MODULE.width,h=settled.height>=0.3?settled.height:MODULE.height;
      const panels=placeOnGrid(field,center,w,h,settled.gap||MODULE.gap);
      return {panels,width:w,height:h,error:panels.length?null:"No south-facing roof face found near the pin. Mark the usable roof manually."};
    } catch(e) {return {panels:[],width:0,height:0,error:e instanceof Error?e.message:"Roof placement failed."};}
  },[field,center,job.origin,settled,roof]);
  const shown=Math.max(0,Math.min(proposedPanels,result.panels.length));
  const clones=useMemo(()=>template?Array.from({length:shown},()=>template.object.clone(true)):[],[template,shown]);
  useEffect(()=>{onLoaded?.();},[onLoaded]);
  // ours: frame the placed panels (the Solar building can sit beside the pin); the pin otherwise
  const focus=useMemo(()=>{
    const first=result.panels.slice(0,20);
    if(!first.length)return center;
    return first.reduce((s,p)=>s.add(new Vector3(...p.position)),new Vector3()).divideScalar(first.length);
  },[result,center]);
  useEffect(()=>{camera.position.set(focus.x+size*0.5,focus.y+size*0.65,focus.z+size*0.6);camera.lookAt(focus);camera.updateProjectionMatrix();invalidate();},[camera,focus,size,invalidate]);
  useEffect(()=>{onReport(result.panels.length,result.error);},[result,onReport]);
  const click=(e:ThreeEvent<MouseEvent>)=>{if(!marking || e.delta>3)return;e.stopPropagation();onPoint(tuple(e.point));};
  return <>
    <primitive object={scene} onClick={click} />
    {result.panels.slice(0,shown).map((p,i)=>{
      const q=new Quaternion().setFromRotationMatrix(new Matrix4().makeBasis(new Vector3(...p.u),new Vector3(...p.v),new Vector3(...p.normal)));
      // 2 cm gaps: each module is drawn 2 cm smaller than its slot
      return template&&clones[i]
        ? <group key={i} position={p.position} quaternion={q} scale={[(result.width-0.02)/template.width,(result.height-0.02)/template.height,1]}><primitive object={clones[i]} /></group>
        : <mesh key={i} position={p.position} quaternion={q}><boxGeometry args={[result.width-0.02,result.height-0.02,0.04]} /><primitive object={GLASS} attach="material" /></mesh>;
    })}
    {layout.surfaces.flatMap((s,i)=>[<Line key={`roof-${i}`} points={[...s.outline,s.outline[0]]} color="#2563eb" lineWidth={2} />,...s.exclusions.map((p,j)=><Line key={`hole-${i}-${j}`} points={[...p,p[0]]} color="#d97706" lineWidth={3} />)])}
    {draft.length>1 && <Line points={draft} color="#2563eb" lineWidth={3} />}
    {draft.map((p,i)=><mesh key={`draft-${i}`} position={p}><sphereGeometry args={[0.13,8,8]} /><meshBasicMaterial color="#2563eb" /></mesh>)}
    <OrbitControls target={focus} makeDefault enableDamping minDistance={3} maxDistance={size*3} />
  </>;
}

export default function RealHouseScene(props:Props) {
  return <Canvas frameloop="demand" camera={{position:[40,50,40],near:0.1,far:10000}} dpr={[1,1.5]} aria-label="Actual building with preliminary panel placement">
    <hemisphereLight args={["#ffffff","#ddd8c9",2]} /><directionalLight position={[30,60,20]} intensity={2} />
    <Suspense fallback={null}><Building {...props} /></Suspense>
  </Canvas>;
}
