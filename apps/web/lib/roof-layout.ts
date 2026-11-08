import { Vector3 } from "three";
import type { HouseLayout, RoofSurface, Vec3 } from "./real-house";

type Point2 = [number, number];
export type PanelPlacement = { position: Vec3; u: Vec3; v: Vec3; normal: Vec3 };
const vec = (p: Vec3) => new Vector3(...p);
const tuple = (v: Vector3): Vec3 => [v.x, v.y, v.z];
const cross2 = (a: Point2, b: Point2, c: Point2) => (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
const edges = (p: Point2[]) => p.map((a, i) => [a, p[(i+1)%p.length]] as const);
function pointSegment(p: Point2, a: Point2, b: Point2): number {
  const dx=b[0]-a[0], dy=b[1]-a[1], len=dx*dx+dy*dy;
  const t=len ? Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/len)) : 0;
  return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy);
}
function intersects(a: Point2,b: Point2,c: Point2,d: Point2) {
  const ab1=cross2(a,b,c),ab2=cross2(a,b,d),cd1=cross2(c,d,a),cd2=cross2(c,d,b);
  if (ab1*ab2<0 && cd1*cd2<0) return true;
  return Math.min(pointSegment(a,c,d),pointSegment(b,c,d),pointSegment(c,a,b),pointSegment(d,a,b))<1e-8;
}
function inside(p: Point2, poly: Point2[]) {
  let result=false;
  for(let i=0,j=poly.length-1;i<poly.length;j=i++) {
    const a=poly[i],b=poly[j];
    if(pointSegment(p,a,b)<1e-8) return true;
    if((a[1]>p[1])!==(b[1]>p[1]) && p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]) result=!result;
  }
  return result;
}
function edgeDistance(a: Point2,b: Point2,c: Point2,d: Point2) {
  return intersects(a,b,c,d)?0:Math.min(pointSegment(a,c,d),pointSegment(b,c,d),pointSegment(c,a,b),pointSegment(d,a,b));
}
function validPolygon(p: Point2[]) {
  if(p.length<3 || p.some(v=>v.some(x=>!Number.isFinite(x)))) return false;
  if(edges(p).some(([a,b])=>Math.hypot(a[0]-b[0],a[1]-b[1])<0.05)) return false;
  const area=Math.abs(edges(p).reduce((s,[a,b])=>s+a[0]*b[1]-a[1]*b[0],0))/2;
  if(area<0.001) return false;
  const es=edges(p);
  return !es.some(([a,b],i)=>es.some(([c,d],j)=>j>i+1 && !(i===0&&j===es.length-1) && intersects(a,b,c,d)));
}
export function surfaceFrame(surface: RoofSurface) {
  const outline=surface.outline;
  if(outline.length<3 || outline.some(p=>p.length!==3 || p.some(x=>!Number.isFinite(x)))) throw new Error("Mark at least three finite roof corners.");
  const origin=vec(outline[0]),u=vec(outline[1]).sub(origin).normalize();
  let n=new Vector3();
  for(const p of outline.slice(2)) { n=new Vector3().crossVectors(u,vec(p).sub(origin)); if(n.length()>0.01) break; }
  if(n.length()<0.01) throw new Error("Roof corners must not be in a straight line.");
  n.normalize(); if(n.y<0) n.negate();
  if(n.y<0.3) throw new Error("Select a roof surface, not a wall.");
  const v=new Vector3().crossVectors(n,u).normalize();
  const project=(p: Vec3): Point2=>{ const q=vec(p).sub(origin);return [q.dot(u),q.dot(v)]; };
  const lift=(p:Point2)=>tuple(origin.clone().addScaledVector(u,p[0]).addScaledVector(v,p[1]));
  const poly=outline.map(project);
  if(!validPolygon(poly)) throw new Error("Roof outline crosses itself or has duplicate corners.");
  if(outline.some(p=>Math.abs(vec(p).sub(origin).dot(n))>0.3)) throw new Error("Mark one flat roof face at a time; the corners cross different slopes.");
  return {origin,u,v,n,project,lift,poly};
}
export function packRoof(layout: HouseLayout): PanelPlacement[] {
  const {width,height,gap,setback}=layout;
  if(![width,height,gap,setback].every(Number.isFinite) || width<0.3 || height<0.3 || width>5 || height>5 || gap<0 || gap>1 || setback<0 || setback>5) throw new Error("Enter panel dimensions from 0.3 to 5 m and non-negative spacing/setback.");
  const result: PanelPlacement[]=[];
  for(const surface of layout.surfaces) {
    const f=surfaceFrame(surface), holes=surface.exclusions.map(p=>p.map(f.project));
    if(holes.some(p=>!validPolygon(p))) throw new Error("An exclusion outline is invalid.");
    const xs=f.poly.map(p=>p[0]),ys=f.poly.map(p=>p[1]);
    const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
    if(maxX-minX>200 || maxY-minY>200) throw new Error("The marked roof is too large for this residential planner.");
    let best:PanelPlacement[]=[];
    // Try grids anchored at each corner: one bounding-box origin can miss an otherwise usable triangular roof.
    const nx=Math.max(0,Math.floor((maxX-minX-2*setback+gap+1e-8)/(width+gap)));
    const ny=Math.max(0,Math.floor((maxY-minY-2*setback+gap+1e-8)/(height+gap)));
    for(const right of [false,true]) for(const top of [false,true]) {
      const grid:PanelPlacement[]=[];let attempts=0;
      for(let iy=0;iy<ny;iy++) for(let ix=0;ix<nx;ix++) {
        const x=right?maxX-setback-width-ix*(width+gap):minX+setback+ix*(width+gap);
        const y=top?maxY-setback-height-iy*(height+gap):minY+setback+iy*(height+gap);
        if(++attempts>40_000) throw new Error("Too many candidate positions; check the roof scale and panel dimensions.");
        const rect:Point2[]=[[x,y],[x+width,y],[x+width,y+height],[x,y+height]];
        // Corners alone are insufficient for concave roofs and enclosed obstructions.
        if(!rect.every(p=>inside(p,f.poly))) continue;
        const re=edges(rect),pe=edges(f.poly);
        if(re.some(([a,b])=>pe.some(([c,d])=>edgeDistance(a,b,c,d)<Math.max(setback-1e-7,1e-8)))) continue;
        if(holes.some(h=>rect.some(p=>inside(p,h)) || h.some(p=>inside(p,rect)) || re.some(([a,b])=>edges(h).some(([c,d])=>edgeDistance(a,b,c,d)<Math.max(setback-1e-7,1e-8))))) continue;
        const position=vec(f.lift([x+width/2,y+height/2])).addScaledVector(f.n,0.07);
        const halfDiag=Math.hypot(width,height)/2;
        // Roof faces may overlap; don't put a second panel through an earlier one on the same plane.
        if([...result,...grid].some(p=>Math.abs(vec(p.position).sub(position).dot(f.n))<0.05 && vec(p.position).distanceTo(position)<halfDiag*0.8)) continue;
        grid.push({position:tuple(position),u:tuple(f.u),v:tuple(f.v),normal:tuple(f.n)});
        if(grid.length>=1000) break;
      }
      if(grid.length>best.length)best=grid;
    }
    result.push(...best);if(result.length>=1000)return result.slice(0,1000);
  }
  return result;
}
