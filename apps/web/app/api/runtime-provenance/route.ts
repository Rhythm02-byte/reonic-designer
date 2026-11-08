import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import path from "node:path";
import { isLocalRequest, repoRoot } from "@/lib/lab-server";
export async function GET(req:Request){
  if(!isLocalRequest(req.headers))return Response.json({error:"Runtime provenance is local-only."},{status:403});
  const root=repoRoot();if(!root)return Response.json({runtime:null});
  const read=async(file:string)=>JSON.parse(await readFile(path.join(root,file),"utf8").catch(()=>"null"));
  const runtime=await read(".cache/engine-runtime.json");
  const evaluation=await read(".cache/frozen-evaluation.json");
  if(!runtime)return Response.json({runtime:null,evaluationMatches:false},{headers:{"Cache-Control":"no-store"}});
  let alive=false;try{process.kill(runtime.pid,0);alive=true;}catch{/* old boot record */}
  const diskHash=await readFile(path.join(root,"services/engine/models/designer.joblib")).then(b=>createHash("sha256").update(b).digest("hex")).catch(()=>null);
  const loadedFileMatches=diskHash!==null&&runtime.modelSha256===diskHash;
  return Response.json({runtime:{...runtime,alive,loadedFileMatches},evaluationMatches:Boolean(alive&&loadedFileMatches&&evaluation&&["modelSha256","policySha256","sourceSha256"].every(k=>runtime[k]===evaluation[k])),evaluationGeneratedAt:evaluation?.generatedAt??null},{headers:{"Cache-Control":"no-store"}});
}
