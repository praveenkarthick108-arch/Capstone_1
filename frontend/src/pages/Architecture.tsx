import React, { useState } from 'react';

const C = {
  cyan:   '#00D4FF', cyanD:  'rgba(0,212,255,0.15)',   cyanB:  'rgba(0,212,255,0.35)',
  purple: '#A855F7', purpleD:'rgba(168,85,247,0.15)',  purpleB:'rgba(168,85,247,0.35)',
  green:  '#00FF88', greenD: 'rgba(0,255,136,0.12)',   greenB: 'rgba(0,255,136,0.3)',
  orange: '#FF8C00', orangeD:'rgba(255,140,0,0.12)',   orangeB:'rgba(255,140,0,0.3)',
  red:    '#FF3B3B', redD:   'rgba(255,59,59,0.12)',   redB:   'rgba(255,59,59,0.3)',
  gold:   '#FFD700', goldD:  'rgba(255,215,0,0.12)',   goldB:  'rgba(255,215,0,0.3)',
  bg:     '#0A0E1A', bgCard: 'rgba(255,255,255,0.03)', bgCard2:'rgba(255,255,255,0.06)',
  text:   'rgba(226,232,240,0.9)', textDim: 'rgba(226,232,240,0.45)',
};

// ── Reusable SVG helpers ────────────────────────────────────────────────────────
const Box: React.FC<{
  x:number; y:number; w:number; h:number;
  fill?:string; stroke?:string; r?:number; opacity?:number;
}> = ({x,y,w,h,fill=C.bgCard,stroke=C.cyanB,r=8,opacity=1}) => (
  <rect x={x} y={y} width={w} height={h} rx={r} ry={r}
    fill={fill} stroke={stroke} strokeWidth={1} opacity={opacity} />
);

const Label: React.FC<{
  x:number; y:number; text:string; size?:number; color?:string;
  bold?:boolean; anchor?:'start'|'middle'|'end';
}> = ({x,y,text,size=12,color=C.text,bold=false,anchor='middle'}) => (
  <text x={x} y={y} fontSize={size} fill={color} textAnchor={anchor}
    fontWeight={bold ? 700 : 400} fontFamily="Inter, sans-serif">
    {text}
  </text>
);

const Tag: React.FC<{x:number;y:number;w:number;h:number;text:string;color:string;fill:string}> =
  ({x,y,w,h,text,color,fill}) => (
  <g>
    <rect x={x} y={y} width={w} height={h} rx={4} fill={fill} stroke={color} strokeWidth={1}/>
    <text x={x+w/2} y={y+h/2+4} fontSize={9.5} fill={color} textAnchor="middle"
      fontWeight={600} fontFamily="Inter, sans-serif" letterSpacing="0.5">{text}</text>
  </g>
);

const Arrow: React.FC<{
  x1:number; y1:number; x2:number; y2:number; color?:string; dashed?:boolean;
}> = ({x1,y1,x2,y2,color=C.cyan,dashed=false}) => {
  const angle = Math.atan2(y2 - y1, x2 - x1);
  const len = Math.sqrt((x2-x1)**2 + (y2-y1)**2);
  const ax = x2 - 9*Math.cos(angle);
  const ay = y2 - 9*Math.sin(angle);
  const id = `ah-${x1}-${y1}-${x2}-${y2}`.replace(/\./g,'');
  return (
    <g>
      <defs>
        <marker id={id} markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L0,6 L8,3 z" fill={color}/>
        </marker>
      </defs>
      <line x1={x1} y1={y1} x2={ax} y2={ay} stroke={color} strokeWidth={1.5}
        strokeDasharray={dashed ? '5,4' : undefined}
        markerEnd={`url(#${id})`} opacity={0.8}/>
    </g>
  );
};

const BendArrow: React.FC<{
  x1:number; y1:number; x2:number; y2:number; color?:string; dashed?:boolean;
}> = ({x1,y1,x2,y2,color=C.cyan,dashed=false}) => {
  const mx = x1; const my = y2;
  const id = `ba-${x1}-${y1}-${x2}-${y2}`.replace(/\./g,'');
  return (
    <g>
      <defs>
        <marker id={id} markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L0,6 L8,3 z" fill={color}/>
        </marker>
      </defs>
      <path d={`M${x1} ${y1} L${mx} ${my} L${x2-8} ${y2}`}
        fill="none" stroke={color} strokeWidth={1.5}
        strokeDasharray={dashed ? '5,4' : undefined}
        markerEnd={`url(#${id})`} opacity={0.8}/>
    </g>
  );
};

// ── SYSTEM ARCHITECTURE DIAGRAM ────────────────────────────────────────────────
const SystemArchDiagram: React.FC = () => {
  const W = 1380; const H = 1000;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{width:'100%',height:'auto',display:'block'}}>
      {/* ── Background ── */}
      <rect width={W} height={H} fill={C.bg}/>

      {/* ── Title ── */}
      <Label x={W/2} y={38} text="SYSTEM ARCHITECTURE — TELECOMIQ FAULT INTELLIGENCE PLATFORM"
        size={15} color={C.cyan} bold anchor="middle"/>
      <line x1={60} y1={48} x2={W-60} y2={48} stroke={C.cyanB} strokeWidth={1}/>

      {/* ══════════════════ FRONTEND LAYER ══════════════════ */}
      <Box x={20} y={62} w={W-40} h={130} fill="rgba(0,212,255,0.04)" stroke={C.cyanB} r={10}/>
      <Label x={50} y={82} text="BROWSER  /  FRONTEND" size={10} color={C.cyan} bold anchor="start"/>
      <Label x={50} y={96} text="React 18 + TypeScript + Recharts + Framer Motion" size={9} color={C.textDim} anchor="start"/>

      {/* Frontend component boxes */}
      {[
        {x:40,  label:'Fault Analysis', sub:'SSE Streaming', c:C.cyan,  f:C.cyanD,  b:C.cyanB},
        {x:235, label:'Analytics',      sub:'Dashboard',     c:C.cyan,  f:C.cyanD,  b:C.cyanB},
        {x:430, label:'Query History',  sub:'localStorage',  c:C.cyan,  f:C.cyanD,  b:C.cyanB},
        {x:625, label:'Follow-up Q&A',  sub:'Chat Thread',   c:C.purple,f:C.purpleD,b:C.purpleB},
        {x:820, label:'Voice Input',    sub:'Web Speech API',c:C.green, f:C.greenD, b:C.greenB},
        {x:1015,label:'Explainability', sub:'WHY RETRIEVED', c:C.gold,  f:C.goldD,  b:C.goldB},
        {x:1210,label:'Export Report',  sub:'Markdown / .md',c:C.orange,f:C.orangeD,b:C.orangeB},
      ].map(({x,label,sub,c,f,b})=>(
        <g key={label}>
          <Box x={x} y={108} w={170} h={72} fill={f} stroke={b} r={8}/>
          <Label x={x+85} y={133} text={label} size={11} color={c} bold/>
          <Label x={x+85} y={150} text={sub} size={9} color={C.textDim}/>
        </g>
      ))}

      {/* Frontend → Backend arrows */}
      <Arrow x1={125} y1={180} x2={125} y2={228} color={C.cyan}/>
      <Arrow x1={700} y1={180} x2={700} y2={228} color={C.cyan}/>
      <Arrow x1={1140} y1={180} x2={1140} y2={228} color={C.orange} dashed/>
      <Label x={W/2} y={210} text="HTTP REST · Server-Sent Events (SSE) · WebFetch" size={9} color={C.textDim}/>

      {/* ══════════════════ BACKEND LAYER ══════════════════ */}
      <Box x={20} y={228} w={W-40} h={490} fill="rgba(0,102,204,0.04)" stroke="rgba(0,102,204,0.35)" r={10}/>
      <Label x={50} y={248} text="FASTAPI BACKEND" size={10} color="#4A9EFF" bold anchor="start"/>
      <Label x={50} y={262} text="Python 3.12 · Uvicorn · Pydantic v2 · Async/Await" size={9} color={C.textDim} anchor="start"/>

      {/* ── Request Pipeline ── */}
      <Box x={40} y={272} w={1300} h={95} fill="rgba(255,255,255,0.02)" stroke="rgba(255,255,255,0.08)" r={8}/>
      <Label x={70} y={290} text="REQUEST PIPELINE" size={9} color={C.textDim} bold anchor="start"/>
      {[
        {x:55,  label:'Input Guardrails',   sub:'PII · Injection · Telecom Keywords', c:C.red,    f:C.redD,   b:C.redB},
        {x:350, label:'Query Enhancement',  sub:'LLM Rewrite · Region / Tech Extract', c:C.gold,  f:C.goldD,  b:C.goldB},
        {x:645, label:'Anomaly Detection',  sub:'Baseline vs Recent Rate',             c:C.orange, f:C.orangeD,b:C.orangeB},
        {x:940, label:'API Endpoints',      sub:'/stream · /query · /followup',        c:'#4A9EFF',f:'rgba(74,158,255,0.1)',b:'rgba(74,158,255,0.3)'},
      ].map(({x,label,sub,c,f,b})=>(
        <g key={label}>
          <Box x={x} y={298} w={280} h={58} fill={f} stroke={b} r={7}/>
          <Label x={x+140} y={321} text={label} size={10.5} color={c} bold/>
          <Label x={x+140} y={338} text={sub} size={8.5} color={C.textDim}/>
        </g>
      ))}
      <Arrow x1={335} y1={327} x2={350} y2={327} color={C.gold}/>
      <Arrow x1={630} y1={327} x2={645} y2={327} color={C.orange}/>
      <Arrow x1={925} y1={327} x2={940} y2={327} color={'#4A9EFF'}/>

      {/* ── Agent Pipeline ── */}
      <Box x={40} y={377} w={1300} h={110} fill="rgba(168,85,247,0.04)" stroke={C.purpleB} r={8}/>
      <Label x={70} y={396} text="MULTI-AGENT PIPELINE  (A2A Communication — Sequential with SSE Streaming)" size={9} color={C.purple} bold anchor="start"/>
      {[
        {x:55,  label:'Alarm Retrieval',   sub:'Top-5 Similar Incidents',         badge:'Agent 1'},
        {x:350, label:'Root Cause Analysis',sub:'Fault Chain · Confidence Score', badge:'Agent 2'},
        {x:645, label:'Service Impact',    sub:'SLA Risk · Revenue · Subscribers',badge:'Agent 3'},
        {x:940, label:'Resolution Planner',sub:'Steps · Commands · Escalation',   badge:'Agent 4'},
      ].map(({x,label,sub,badge},i)=>(
        <g key={label}>
          <Box x={x} y={404} w={280} h={72} fill={C.purpleD} stroke={C.purpleB} r={7}/>
          <Tag x={x+8} y={408} w={52} h={16} text={badge} color={C.purple} fill="rgba(168,85,247,0.2)"/>
          <Label x={x+140} y={438} text={label} size={10.5} color={C.purple} bold/>
          <Label x={x+140} y={453} text={sub} size={8.5} color={C.textDim}/>
          {i < 3 && <Arrow x1={x+280} y1={440} x2={x+280+70} y2={440} color={C.purple}/>}
        </g>
      ))}
      <Label x={W/2} y={490} text="Each agent output becomes input context for the next (A2A)" size={8.5} color={C.textDim}/>

      {/* ── RAG Stack ── */}
      <Box x={40} y={498} w={840} h={106} fill="rgba(0,255,136,0.03)" stroke={C.greenB} r={8}/>
      <Label x={70} y={516} text="HYBRID RAG RETRIEVAL STACK" size={9} color={C.green} bold anchor="start"/>
      {[
        {x:55,  label:'Embeddings',       sub:'text-embedding-3-small'},
        {x:235, label:'Vector Search',    sub:'ChromaDB · Cosine Sim'},
        {x:415, label:'BM25 Keyword',     sub:'rank_bm25 · Term Weights'},
        {x:595, label:'RRF Fusion',       sub:'Reciprocal Rank Fusion'},
        {x:775, label:'LLM Reranker',     sub:'gpt-4o-mini Scored'},
      ].map(({x,label,sub},i)=>(
        <g key={label}>
          <Box x={x} y={524} w={168} h={68} fill={C.greenD} stroke={C.greenB} r={7}/>
          <Label x={x+84} y={551} text={label} size={10} color={C.green} bold/>
          <Label x={x+84} y={566} text={sub} size={8.5} color={C.textDim}/>
          {i < 4 && <Arrow x1={x+168} y1={558} x2={x+168+7} y2={558} color={C.green}/>}
        </g>
      ))}
      <Label x={500} y={613} text="+ Retrieval Explainability (BM25 term scores · vector similarity · method tag)" size={8.5} color={C.textDim}/>

      {/* ── Utilities ── */}
      <Box x={900} y={498} w={440} h={106} fill="rgba(255,215,0,0.03)" stroke={C.goldB} r={8}/>
      <Label x={930} y={516} text="UTILITIES & INTELLIGENCE" size={9} color={C.gold} bold anchor="start"/>
      {[
        {x:908, label:'Query Enhancer',   sub:'LLM Rewrite'},
        {x:1083,label:'Outage Predictor', sub:'SLA · Risk Score'},
        {x:1258,label:'Evaluation',       sub:'RAG Quality Metrics'},
      ].map(({x,label,sub})=>(
        <g key={label}>
          <Box x={x} y={524} w={162} h={68} fill={C.goldD} stroke={C.goldB} r={7}/>
          <Label x={x+81} y={551} text={label} size={10} color={C.gold} bold/>
          <Label x={x+81} y={566} text={sub} size={8.5} color={C.textDim}/>
        </g>
      ))}

      {/* ── Integrations ── */}
      <Box x={40} y={615} w={1300} h={88} fill="rgba(255,59,59,0.03)" stroke={C.redB} r={8}/>
      <Label x={70} y={633} text="INTEGRATIONS" size={9} color={C.red} bold anchor="start"/>
      {[
        {x:55,  label:'ServiceNow REST',  sub:'Incident Tickets · NOC Automation', c:C.red,    f:C.redD,   b:C.redB},
        {x:350, label:'LLM Gateway',      sub:'keygateway.arshnivlabs.com',         c:C.gold,   f:C.goldD,  b:C.goldB},
        {x:645, label:'Feedback Store',   sub:'SQLite · Rating · Improvement',      c:C.orange, f:C.orangeD,b:C.orangeB},
        {x:940, label:'Prediction Engine',sub:'Region + Tech Risk Forecasting',     c:C.purple, f:C.purpleD,b:C.purpleB},
      ].map(({x,label,sub,c,f,b})=>(
        <g key={label}>
          <Box x={x} y={641} w={280} h={56} fill={f} stroke={b} r={7}/>
          <Label x={x+140} y={663} text={label} size={10.5} color={c} bold/>
          <Label x={x+140} y={678} text={sub} size={8.5} color={C.textDim}/>
        </g>
      ))}

      {/* Backend → Data arrows */}
      <Arrow x1={200} y1={718} x2={200} y2={758} color={C.orange}/>
      <Arrow x1={700} y1={718} x2={700} y2={758} color={C.orange}/>
      <Arrow x1={1200} y1={718} x2={1200} y2={758} color={C.red} dashed/>

      {/* ══════════════════ DATA LAYER ══════════════════ */}
      <Box x={20} y={730} w={W-40} h={130} fill="rgba(255,140,0,0.04)" stroke={C.orangeB} r={10}/>
      <Label x={50} y={750} text="DATA LAYER" size={10} color={C.orange} bold anchor="start"/>
      <Label x={50} y={764} text="Persistent storage and knowledge base" size={9} color={C.textDim} anchor="start"/>
      {[
        {x:40,  label:'ChromaDB',        sub:'7,400 incidents · Cosine Index · Metadata Filters',           c:C.orange, f:C.orangeD, b:C.orangeB},
        {x:355, label:'BM25 Index',      sub:'Pickle file · Tokenized corpus · IDF weights',                c:C.orange, f:C.orangeD, b:C.orangeB},
        {x:670, label:'CSV Dataset',     sub:'Telstra incidents + 19 synthetic 5G-NR · 7,400 rows',         c:C.orange, f:C.orangeD, b:C.orangeB},
        {x:985, label:'localStorage',    sub:'Query history (20 entries) · React client-side',              c:C.cyan,   f:C.cyanD,   b:C.cyanB},
      ].map(({x,label,sub,c,f,b})=>(
        <g key={label}>
          <Box x={x} y={776} w={300} h={70} fill={f} stroke={b} r={7}/>
          <Label x={x+150} y={803} text={label} size={11} color={c} bold/>
          <Label x={x+150} y={820} text={sub} size={8.5} color={C.textDim}/>
        </g>
      ))}

      {/* Legend */}
      <Box x={20} y={878} w={W-40} h={112} fill="rgba(255,255,255,0.02)" stroke="rgba(255,255,255,0.06)" r={8}/>
      <Label x={50} y={897} text="LEGEND" size={9} color={C.textDim} bold anchor="start"/>
      {[
        {x:40,  c:C.cyan,   label:'Frontend / UI'},
        {x:200, c:C.purple, label:'AI Agents'},
        {x:360, c:C.green,  label:'RAG Stack'},
        {x:520, c:C.gold,   label:'LLM Gateway'},
        {x:680, c:C.orange, label:'Data Storage'},
        {x:840, c:C.red,    label:'External Services'},
        {x:1020,c:'#4A9EFF',label:'API Layer'},
      ].map(({x,c,label})=>(
        <g key={label}>
          <rect x={x} y={908} width={16} height={16} rx={4} fill={c} opacity={0.7}/>
          <text x={x+22} y={920} fontSize={10} fill={C.textDim} fontFamily="Inter, sans-serif">{label}</text>
        </g>
      ))}
      <Label x={40} y={960} text="→  Synchronous call    ···►  Asynchronous / Optional    SSE  Server-Sent Events (streaming)    A2A  Agent-to-Agent communication"
        size={9} color={C.textDim} anchor="start"/>
    </svg>
  );
};

// ── DATA FLOW DIAGRAM ────────────────────────────────────────────────────────────
const DataFlowDiagram: React.FC = () => {
  const W = 1380; const H = 920;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{width:'100%',height:'auto',display:'block'}}>
      <rect width={W} height={H} fill={C.bg}/>

      {/* Title */}
      <Label x={W/2} y={36} text="DATA FLOW DIAGRAM — QUERY-TO-RESPONSE PIPELINE"
        size={15} color={C.purple} bold/>
      <line x1={60} y1={46} x2={W-60} y2={46} stroke={C.purpleB} strokeWidth={1}/>

      {/* ── COLUMN LAYOUT ──
          col 1: x=40-240   (input)
          col 2: x=280-540  (validation)
          col 3: x=580-840  (retrieval)
          col 4: x=880-1140 (agents)
          col 5: x=1180-W   (output)
      */}

      {/* Phase headers */}
      {[
        {x:60,   label:'① INPUT',       sub:'User Interface',          c:C.cyan,   f:C.cyanD},
        {x:300,  label:'② VALIDATION',  sub:'Safety & Enhancement',    c:C.gold,   f:C.goldD},
        {x:570,  label:'③ RETRIEVAL',   sub:'Hybrid RAG Search',       c:C.green,  f:C.greenD},
        {x:850,  label:'④ AGENTS',      sub:'A2A Pipeline (SSE)',      c:C.purple, f:C.purpleD},
        {x:1150, label:'⑤ OUTPUT',      sub:'Response & Actions',      c:C.orange, f:C.orangeD},
      ].map(({x,label,sub,c,f})=>(
        <g key={label}>
          <rect x={x} y={58} width={220} height={48} rx={8} fill={f} stroke={c} strokeWidth={1} opacity={0.7}/>
          <text x={x+110} y={79} fontSize={12} fill={c} textAnchor="middle" fontWeight={700} fontFamily="Inter">{label}</text>
          <text x={x+110} y={96} fontSize={9} fill={C.textDim} textAnchor="middle" fontFamily="Inter">{sub}</text>
        </g>
      ))}

      {/* ── MAIN FLOW BOXES ── */}

      {/* Step 1: User Query */}
      <Box x={50} y={130} w={200} h={70} fill={C.cyanD} stroke={C.cyanB} r={10}/>
      <Label x={150} y={155} text="Natural Language Query" size={10.5} color={C.cyan} bold/>
      <Label x={150} y={172} text="Text Input / Voice (Web Speech)" size={8.5} color={C.textDim}/>
      <Label x={150} y={186} text="e.g. '5G not working in Chennai'" size={8} color={C.textDim}/>

      {/* Step 1b: Voice */}
      <Box x={50} y={220} w={200} h={55} fill={C.greenD} stroke={C.greenB} r={8}/>
      <Label x={150} y={242} text="Voice Input" size={10.5} color={C.green} bold/>
      <Label x={150} y={258} text="SpeechRecognition API → text" size={8.5} color={C.textDim}/>

      {/* Arrow: Input → Guardrails */}
      <Arrow x1={250} y1={165} x2={300} y2={165} color={C.cyan}/>

      {/* Step 2a: Guardrails */}
      <Box x={300} y={130} w={220} h={70} fill={C.redD} stroke={C.redB} r={10}/>
      <Label x={410} y={152} text="Input Guardrails" size={10.5} color={C.red} bold/>
      <Label x={410} y={168} text="PII detection · SQL injection" size={8.5} color={C.textDim}/>
      <Label x={410} y={182} text="Telecom keyword filter" size={8.5} color={C.textDim}/>

      {/* Reject branch */}
      <Arrow x1={410} y1={200} x2={410} y2={240} color={C.red}/>
      <Box x={310} y={240} w={200} h={50} fill="rgba(255,59,59,0.08)" stroke={C.redB} r={7}/>
      <Label x={410} y={261} text="422 Rejected" size={10} color={C.red} bold/>
      <Label x={410} y={276} text="Clear error message to UI" size={8.5} color={C.textDim}/>

      {/* Step 2b: Query Enhancement */}
      <Arrow x1={520} y1={165} x2={565} y2={165} color={C.gold}/>
      <Box x={565} y={130} w={220} h={70} fill={C.goldD} stroke={C.goldB} r={10}/>
      <Label x={675} y={152} text="Query Enhancement" size={10.5} color={C.gold} bold/>
      <Label x={675} y={168} text="LLM rewrites to technical terms" size={8.5} color={C.textDim}/>
      <Label x={675} y={182} text="Extracts: region / tech / severity" size={8.5} color={C.textDim}/>

      {/* Enhancement output badge */}
      <Box x={575} y={215} w={200} h={45} fill="rgba(255,215,0,0.08)" stroke={C.goldB} r={6}/>
      <Label x={675} y={234} text='"5g south" → gNB Connectivity' size={9} color={C.gold}/>
      <Label x={675} y={249} text='Failure + Region=South + 5G-NR' size={9} color={C.gold}/>

      {/* ── RETRIEVAL STAGE ── */}
      <Arrow x1={785} y1={165} x2={835} y2={165} color={C.green}/>

      {/* Vector Search */}
      <Box x={835} y={100} w={210} h={75} fill={C.greenD} stroke={C.greenB} r={10}/>
      <Label x={940} y={122} text="Vector Search" size={10.5} color={C.green} bold/>
      <Label x={940} y={138} text="text-embedding-3-small → query vec" size={8.5} color={C.textDim}/>
      <Label x={940} y={152} text="ChromaDB cosine sim → top-20" size={8.5} color={C.textDim}/>
      <Label x={940} y={166} text="+ Metadata filter (region/tech)" size={8.5} color={C.textDim}/>

      {/* BM25 Search */}
      <Box x={835} y={190} w={210} h={75} fill={C.greenD} stroke={C.greenB} r={10}/>
      <Label x={940} y={212} text="BM25 Keyword Search" size={10.5} color={C.green} bold/>
      <Label x={940} y={228} text="Tokenize query → IDF scoring" size={8.5} color={C.textDim}/>
      <Label x={940} y={244} text="rank_bm25 → top-20 candidates" size={8.5} color={C.textDim}/>
      <Label x={940} y={258} text="BM25-only fallback if embed fails" size={8.5} color={C.textDim}/>

      {/* RRF Fusion */}
      <Arrow x1={1045} y1={138} x2={1095} y2={200} color={C.green}/>
      <Arrow x1={1045} y1={228} x2={1095} y2={216} color={C.green}/>
      <Box x={1090} y={170} w={190} h={70} fill="rgba(0,255,136,0.1)" stroke={C.greenB} r={10}/>
      <Label x={1185} y={193} text="RRF Fusion" size={10.5} color={C.green} bold/>
      <Label x={1185} y={209} text="score = 1/(k+rank_v)+1/(k+rank_b)" size={8} color={C.textDim}/>
      <Label x={1185} y={223} text="Top-10 fused candidates" size={8.5} color={C.textDim}/>

      {/* Reranker */}
      <Arrow x1={1185} y1={240} x2={1185} y2={270} color={C.green}/>
      <Box x={1090} y={270} w={190} h={70} fill={C.greenD} stroke={C.greenB} r={10}/>
      <Label x={1185} y={293} text="LLM Reranker" size={10.5} color={C.green} bold/>
      <Label x={1185} y={309} text="gpt-4o-mini cross-encoder score" size={8.5} color={C.textDim}/>
      <Label x={1185} y={323} text="Top-5 + retrieval explanation" size={8.5} color={C.textDim}/>

      {/* ── AGENT PIPELINE (vertical) ── */}
      {/* Retrieval → Agent 1 */}
      <Arrow x1={1185} y1={340} x2={1185} y2={380} color={C.purple}/>

      {[
        {y:380, n:'1', label:'Alarm Retrieval Agent',   sub1:'Runs hybrid_search() with filters',      sub2:'Returns top-5 + alarm patterns',        c:C.purple},
        {y:475, n:'2', label:'Root Cause Agent',        sub1:'Input: query + retrieved incidents',     sub2:'Output: fault chain + confidence %',     c:C.purple},
        {y:570, n:'3', label:'Service Impact Agent',    sub1:'Input: retrieval + RCA results',        sub2:'Output: SLA risk + subscribers + revenue',c:C.purple},
        {y:665, n:'4', label:'Resolution Planner',      sub1:'Input: all prior agent context',        sub2:'Output: steps + CLI commands + escalation',c:C.purple},
      ].map(({y,n,label,sub1,sub2,c},i)=>(
        <g key={n}>
          <Box x={1090} y={y} w={240} h={80} fill={C.purpleD} stroke={C.purpleB} r={10}/>
          <Tag x={1098} y={y+6} w={52} h={16} text={`Agent ${n}`} color={c} fill="rgba(168,85,247,0.25)"/>
          {/* SSE badge */}
          <Tag x={1158} y={y+6} w={32} h={16} text="SSE" color={C.cyan} fill={C.cyanD}/>
          <Label x={1210} y={y+38} text={label} size={10.5} color={c} bold/>
          <Label x={1210} y={y+53} text={sub1} size={8.5} color={C.textDim}/>
          <Label x={1210} y={y+66} text={sub2} size={8.5} color={C.textDim}/>
          {i < 3 && <Arrow x1={1210} y1={y+80} x2={1210} y2={y+95} color={C.purple}/>}
          {/* SSE event line to right side */}
          <line x1={1330} y1={y+40} x2={1370} y2={y+40} stroke={C.cyan} strokeWidth={1} strokeDasharray="3,3" opacity={0.5}/>
        </g>
      ))}

      {/* Post-processing */}
      <Arrow x1={1210} y1={745} x2={1210} y2={775} color={C.cyan}/>
      <Box x={1090} y={775} w={240} h={70} fill={C.cyanD} stroke={C.cyanB} r={10}/>
      <Label x={1210} y={800} text="Post-Processing" size={10.5} color={C.cyan} bold/>
      <Label x={1210} y={816} text="Anomaly detection · Chain fixing" size={8.5} color={C.textDim}/>
      <Label x={1210} y={830} text="SLA escalation · Unknown fills" size={8.5} color={C.textDim}/>

      {/* SSE stream → UI label */}
      <line x1={1370} y1={380} x2={1370} y2={845} stroke={C.cyan} strokeWidth={1.5} strokeDasharray="4,3" opacity={0.4}/>
      <Arrow x1={1370} y1={845} x2={1330} y2={845} color={C.cyan}/>
      <Box x={1090} y={858} w={240} h={52} fill={C.cyanD} stroke={C.cyanB} r={8}/>
      <Label x={1210} y={879} text="SSE → Frontend" size={10.5} color={C.cyan} bold/>
      <Label x={1210} y={895} text="Progressive UI update per agent" size={8.5} color={C.textDim}/>
      <Label x={1370} y={610} text="SSE" size={9} color={C.cyan} bold anchor="middle"/>

      {/* ── LEFT SIDE VERTICAL FLOW LABELS ── */}
      <line x1={30} y1={130} x2={30} y2={850} stroke="rgba(255,255,255,0.06)" strokeWidth={1} strokeDasharray="4,4"/>

      {/* Step numbers on left rail */}
      {[
        {y:165, n:'① Input'},
        {y:300, n:'② Validate'},
        {y:430, n:'③ Retrieve'},
        {y:560, n:'④ Agents'},
        {y:845, n:'⑤ Output'},
      ].map(({y,n})=>(
        <g key={n}>
          <circle cx={30} cy={y} r={14} fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.15)" strokeWidth={1}/>
          <text x={30} y={y+4} fontSize={8} fill={C.textDim} textAnchor="middle" fontFamily="Inter">{n.split(' ')[0]}</text>
        </g>
      ))}

      {/* Legends at bottom */}
      <Box x={20} y={900} w={W-40} h={16} fill="rgba(0,0,0,0)" stroke="rgba(255,255,255,0)" r={0}/>
      <Label x={W/2} y={913} text="→ Synchronous  ···► Async/Optional  SSE Server-Sent Events stream per agent  A2A Agent context passed sequentially  RRF Reciprocal Rank Fusion  BM25 Best Match 25"
        size={8.5} color={C.textDim}/>
    </svg>
  );
};

// ── PAGE ──────────────────────────────────────────────────────────────────────
const Architecture: React.FC = () => {
  const [active, setActive] = useState<'arch'|'flow'>('arch');

  return (
    <div style={{ maxWidth: 1440, margin: '0 auto', padding: '32px 24px' }}>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#fff' }}>Architecture & Design</h2>
        <p style={{ margin: '6px 0 0', fontSize: 13, color: 'rgba(226,232,240,0.45)' }}>
          Two distinct diagrams — use the tabs to switch between them
        </p>
      </div>

      {/* Callout: two diagrams are DIFFERENT */}
      <div style={{ marginBottom: 16, padding: '12px 16px', borderRadius: 10, background: 'rgba(0,212,255,0.04)', border: '1px solid rgba(0,212,255,0.15)', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 260 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#00D4FF', marginBottom: 4, letterSpacing: '0.5px' }}>① SYSTEM ARCHITECTURE DIAGRAM</div>
          <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.55)', lineHeight: 1.6 }}>
            <em>What exists</em> — Shows all 30+ components organized by tier: Frontend · API · Agents · RAG Stack · Data Layer · External Services. Color-coded: Cyan=UI · Purple=Agents · Green=RAG · Orange=Data.
          </div>
        </div>
        <div style={{ width: 1, background: 'rgba(255,255,255,0.08)', flexShrink: 0 }} />
        <div style={{ flex: 1, minWidth: 260 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#A855F7', marginBottom: 4, letterSpacing: '0.5px' }}>② DATA FLOW DIAGRAM</div>
          <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.55)', lineHeight: 1.6 }}>
            <em>How a query travels</em> — Traces a single fault query through 5 phases: Input → Validation → Retrieval → Agents → Output. Shows branching paths, SSE events, A2A context passing.
          </div>
        </div>
      </div>

      {/* Tab toggle */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {([
          {id:'arch' as const, label:'① System Architecture', color:'#00D4FF'},
          {id:'flow' as const, label:'② Data Flow',           color:'#A855F7'},
        ]).map(({id,label,color})=>(
          <button key={id} onClick={()=>setActive(id)} style={{
            padding: '9px 22px', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600, transition: 'all 0.2s',
            background: active===id ? `${color}22` : 'rgba(255,255,255,0.04)',
            color: active===id ? color : 'rgba(226,232,240,0.5)',
            outline: active===id ? `1px solid ${color}55` : '1px solid transparent',
          }}>{label}</button>
        ))}
        <div style={{ marginLeft: 'auto', fontSize: 11, color: 'rgba(226,232,240,0.3)', alignSelf: 'center' }}>
          {active === 'arch' ? 'Showing: what the system is made of' : 'Showing: how a query moves through the system'}
        </div>
      </div>

      {/* Diagram */}
      <div style={{ background: '#0A0E1A', borderRadius: 12, border: '1px solid rgba(255,255,255,0.07)', overflow: 'hidden' }}>
        {active === 'arch' ? <SystemArchDiagram /> : <DataFlowDiagram />}
      </div>

      {/* Component inventory */}
      <div style={{ marginTop: 24, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12 }}>
        {[
          { title: 'Frontend Stack', color: C.cyan, items: [
            'React 18 + TypeScript + Tailwind CSS',
            'Recharts — donut, bar, line, radar charts',
            'SSE streaming (fetch + ReadableStream)',
            'Web Speech API — voice input',
            'Lucide React icons',
          ]},
          { title: 'Backend Stack', color: '#4A9EFF', items: [
            'FastAPI + Uvicorn (ASGI) + Pydantic v2',
            'OpenAI SDK via keygateway (gpt-4o-mini)',
            'rank_bm25 — keyword index + explainability',
            'ChromaDB — persistent vector store',
            'pandas + numpy — analytics + predictions',
          ]},
          { title: 'AI / Intelligence', color: C.purple, items: [
            'gpt-4o-mini — 4 agents + reranker + Q&A',
            'text-embedding-3-small (1536-dim)',
            'RRF Hybrid Search (vector + BM25)',
            'LLM cross-encoder reranker',
            'A2A context passing — sequential pipeline',
          ]},
          { title: 'Innovations', color: C.green, items: [
            'SSE streaming per-agent events',
            'Retrieval explainability (BM25 terms + sim%)',
            'Semantic query cache (88% cosine threshold)',
            'Anomaly detection — baseline vs recent rate',
            'Green AI score — 97% token reduction',
          ]},
          { title: 'Operations', color: C.orange, items: [
            'ServiceNow REST API — structured NOC tickets',
            'One-click Export Report (.md download)',
            'SLA countdown timer (live, per-second)',
            'Confidence breakdown popover',
            'Query history — localStorage (20 entries)',
          ]},
          { title: 'Data Layer', color: C.gold, items: [
            '7,400 Telstra real network incidents',
            '19 synthetic 5G-NR incidents (augmented)',
            'ChromaDB cosine index + metadata filters',
            'BM25 pickle — IDF weights + term scores',
            'SQLite feedback store',
          ]},
        ].map(({title,color,items})=>(
          <div key={title} style={{ padding: '16px 18px', background: 'rgba(255,255,255,0.02)', borderRadius: 10, border: '1px solid rgba(255,255,255,0.07)' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color, marginBottom: 10, letterSpacing: '0.3px' }}>{title}</div>
            {items.map(item=>(
              <div key={item} style={{ display: 'flex', gap: 8, marginBottom: 6, alignItems: 'flex-start' }}>
                <span style={{ color, fontSize: 10, marginTop: 2 }}>▸</span>
                <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.65)', lineHeight: 1.4 }}>{item}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Architecture;
