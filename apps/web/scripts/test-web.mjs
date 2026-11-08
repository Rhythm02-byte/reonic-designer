// Focused Node behavior checks; transpile the same TS helpers without generating tracked files.
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import assert from "node:assert/strict";
import { test } from "node:test";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const require=createRequire(path.join(root,"package.json"));
const Module=require("node:module"),ts=require("typescript");
const originalResolve=Module._resolveFilename;
Module._resolveFilename=function(name,...args){return originalResolve.call(this,name.startsWith("@/")?path.join(root,name.slice(2)):name,...args);};
Module._extensions[".ts"]=(module,filename)=>module._compile(ts.transpileModule(readFileSync(filename,"utf8"),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX}}).outputText,filename);
const {packRoof,surfaceFrame}=require("./lib/roof-layout.ts");
const {comparable,scored,researchPair,parseHistory}=require("./lib/lab.ts");
const {isLocalMutation}=require("./lib/lab-server.ts");
const surface={outline:[[0,4,0],[6,4,0],[6,4,6],[0,4,6]],exclusions:[]};
const layout={width:1,height:2,gap:0.02,setback:0.3,surfaces:[surface]};

test("panel packing uses actual metre-scale roof and honours edge clearance",()=>{
  const panels=packRoof(layout);assert.equal(panels.length,10);
  for(const p of panels){assert.ok(p.position[0]>=0.8-1e-8&&p.position[0]<=5.2+1e-8);assert.ok(p.position[2]>=1.3-1e-8&&p.position[2]<=4.7+1e-8);assert.ok(Math.abs(p.position[1]-4.07)<1e-8);}
});
test("enclosed chimney rejects a panel even when every panel corner misses the chimney",()=>{
  const large={...layout,width:3,height:3,setback:0.1,surfaces:[{outline:[[0,4,0],[3.5,4,0],[3.5,4,3.5],[0,4,3.5]],exclusions:[[[1.4,4,1.4],[1.6,4,1.4],[1.6,4,1.6],[1.4,4,1.6]]]}]};
  assert.equal(packRoof(large).length,0);
});
test("sloped roof panels lie on that roof plane rather than a flat fallback",()=>{
  const slope={outline:[[0,0,0],[6,0,0],[6,3,6],[0,3,6]],exclusions:[]};const frame=surfaceFrame(slope);
  const panels=packRoof({...layout,surfaces:[slope]});assert.ok(panels.length>0);
  for(const p of panels){const offset=p.position.map((v,i)=>v-slope.outline[0][i]);assert.ok(Math.abs(frame.n.x*offset[0]+frame.n.y*offset[1]+frame.n.z*offset[2]-0.07)<1e-7);}
});
test("invalid walls, crossed outlines and non-finite dimensions fail visibly",()=>{
  assert.throws(()=>packRoof({...layout,width:NaN}));
  assert.throws(()=>packRoof({...layout,surfaces:[{outline:[[0,0,0],[0,6,0],[0,6,6]],exclusions:[]}]}),/wall/);
  assert.throws(()=>packRoof({...layout,surfaces:[{outline:[[0,4,0],[6,4,6],[0,4,6],[6,4,0]],exclusions:[]}]}),/cross|duplicate/);
});
test("concave roof cannot be bridged by a panel rectangle",()=>{
  const s={outline:[[0,4,0],[6,4,0],[6,4,2],[2,4,2],[2,4,6],[0,4,6]],exclusions:[]};
  const panels=packRoof({...layout,width:1,height:1,surfaces:[s]});assert.ok(panels.length>0);
  for(const p of panels) assert.ok(p.position[0]+0.5<=2+1e-8 || p.position[2]+0.5<=2+1e-8);
});
const run=(extra={})=>({id:"a",timestamp:"2026-11-08T00:00:00Z",kind:"all",git:{branch:"next",commit:"a",dirty:false},testScored:false,validation:{n:232,models:{ours:{wholeDesign:0.2}}},...extra});
test("legacy and different population runs never become a trend",()=>{
  assert.equal(comparable(run(),run()),false);
  assert.equal(comparable(run({comparisonKey:"x"}),run({comparisonKey:"y"})),false);
  assert.equal(comparable(run({comparisonKey:"x"}),run({comparisonKey:"x",validation:{n:921,models:{ours:{wholeDesign:0.2}}}})),false);
  assert.equal(comparable(run({comparisonKey:"x"}),run({comparisonKey:"x"})),true);
});
test("local job endpoints reject requests originating on an unrelated website",()=>{
  const req=origin=>new Request("http://localhost:3000/lab/run",{method:"POST",headers:{host:"localhost:3000",origin}});
  assert.equal(isLocalMutation(req("https://unrelated.example")),false);
  assert.equal(isLocalMutation(req("null")),false);
  assert.equal(isLocalMutation(req("http://localhost:3000")),true);
});
test("arbitrarily named research candidates retain scores and stay out of shipped-policy series",()=>{
  const research=run({kind:"research",validation:{n:921,models:{default:{wholeDesign:0.16},candidate_new:{wholeDesign:0.18}}}});
  assert.equal(scored([run(),research]).length,1);assert.equal(researchPair(research)[1][0],"candidate_new");assert.equal(researchPair(research)[1][1].wholeDesign,0.18);
  assert.equal(parseHistory(JSON.stringify(research)+"\nnot-json").invalid,1);
});
test("stalled engine requests fall back after their deadline",async()=>{
  const original=globalThis.fetch, timeout=AbortSignal.timeout;
  const enginePath=require.resolve("./lib/engine.ts");delete require.cache[enginePath];
  try{
    AbortSignal.timeout=()=>timeout(25);
    globalThis.fetch=(_url,options)=>new Promise((_resolve,reject)=>options.signal.addEventListener("abort",()=>reject(new Error("deadline"))));
    const keepAlive=setTimeout(()=>{},1000);
    try {const result=await require(enginePath).api.meta();assert.equal(result.source,"demo");}finally{clearTimeout(keepAlive);}
  }finally{globalThis.fetch=original;AbortSignal.timeout=timeout;delete require.cache[enginePath];}
});
test("a refused alternative validation cannot become an approved homeowner option",async()=>{
  const original=globalThis.fetch;
  const enginePath=require.resolve("./lib/engine.ts"),apiPath=require.resolve("./lib/api.ts");
  delete require.cache[enginePath];delete require.cache[apiPath];
  try{
    const engine=require(enginePath).api;
    engine.meta=async()=>({source:"live",data:{installers:["synthetic"],targets:[{name:"pvKwp",catalog:[5]},{name:"batteryKwh",catalog:[5]},{name:"heatPumpKw",catalog:[8]},{name:"wallboxKw",catalog:[11]}],fields:[],synthetic:false}});
    engine.design=async()=>({source:"live",data:{sizes:{pvKwp:5,batteryKwh:5,heatPumpKw:0,wallboxKw:0},alternatives:[],confidence:{},reasons:[],flags:[],askNext:[],metrics:null,bom:[]}});
    engine.validate=async()=>{throw new Error("unavailable");};
    const d=await require(apiPath).api.design({annual_consumption_kwh:5200});
    assert.ok(Object.values(d.alternatives).length>0);
    for(const a of Object.values(d.alternatives)){assert.equal(a.validated,false);assert.match(a.flags[0],/Not validated/);}
  }finally{globalThis.fetch=original;delete require.cache[enginePath];delete require.cache[apiPath];}
});
