#!/usr/bin/env python3

import os, random, html
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import numpy as np
from datetime import datetime, timezone
import json

# Configuration and setup
CSV_PATH    = "data/v1_cipherdata_latest.csv"   # Latest version of Cipher Data - update as each row checked
OUTPUT_HTML = "index.html"                       # Main HTML file - GitHub Pages then serves this

# Stable jitter (points don't jump between runs)
random.seed(42)

# Formatting
## Time normalisation & display mapping

TIME_ORDER = [
    "Time 0", "Hour Zero", "First Hour", "First Day", "First Week", "Week 2", "First Month", "Unknown"
]

TIME_TO_DISPLAY = {
    "Time 0": "Hour 0",
    "Hour Zero": "Hour 0",
    "First Hour": "Hour 1",
    "First Day": "Day 1",
    "First Week": "Week 1",
    "Week 2": "Week 2",
    "First Month": "Month 1",
    "Unknown": "Unknown"
}

def norm_time_point(s: str) -> str:
    if not isinstance(s, str):
        return "Unknown"
    t = s.strip()
    low = t.lower()
    if low in {"time 0", "hour zero", "zero", "t=0"}:       return "Time 0"
    if low in {"first hour", "hour 1", "1st hour"}:          return "First Hour"
    if low in {"firsy day"}:                                 return "First Day"
    if low in {"first day", "day 1", "1st day"}:             return "First Day"
    if low in {"first week", "week 1", "1st week"}:          return "First Week"
    if low in {"week 2", "2nd week"}:                        return "Week 2"
    if low in {"first month", "month 1", "1st month"}:       return "First Month"
    if t in TIME_TO_DISPLAY:                                 return t
    return t if len(t) <= 30 else "Unknown"

def split_specialties(s): # Column in csv has multiple specialities for some points, e.g. blood test delays
    if not isinstance(s, str) or not s.strip():
        return ["All"]
    # support both ";" and "," as separators
    return [p.strip() for p in s.replace(",", ";").split(";") if p.strip()] or ["All"]

def safe_str(x): 
    return "" if pd.isna(x) else str(x)

# Load data (latest version of csv)
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"CSV not found at {CSV_PATH}")

df_raw = pd.read_csv(CSV_PATH)

# Rename columns to internal names (df / csv headers)
rename_map = {
    'Reference Title': 'ref_title',
    'Reference Link':  'ref_link',
    'Short Title':     'incident',
    'Description of Patient Harm': 'description',
    'Direct Quote':    'quote',
    'Time Point':      'time_point',
    'Speciality':      'specialty_raw',
    'Technical Domain':'domain',
    'Clinical Impact Score': 'impact'
}

df = df_raw.rename(columns=rename_map)

# Preppin fields for model
df['time_point'] = df['time_point'].apply(norm_time_point)
df.loc[df['time_point'] == "", 'time_point'] = "Unknown"
df['domain'] = df['domain'].fillna("Unknown").replace("", "Unknown")

# Numeric impact for sizing (impact scores from csv)
df['impact'] = pd.to_numeric(df['impact'], errors='coerce').fillna(5).clip(lower=1)

# Expand multi-specialty rows into one row per specialty 
rows = []
for _, r in df.iterrows():
    specialties = split_specialties(safe_str(r.get('specialty_raw', 'All')))
    for sp in specialties:
        rr = r.copy()
        rr['specialty'] = sp
        rows.append(rr)

df2 = pd.DataFrame(rows)

# Flags for styling
df2['is_general'] = df2['specialty'].str.strip().str.lower().eq('all')
df2['is_social']  = df2['ref_title'].astype(str).str.strip().str.lower().eq('social media')

# Build category axes
domains = sorted(df2['domain'].dropna().unique().tolist())

times_in_data = df2['time_point'].dropna().unique().tolist()
time_axis = [t for t in TIME_ORDER if t in times_in_data]

for t in times_in_data:
    if t not in time_axis:
        time_axis.append(t)

# All clinical specialities present in specialty column
specialties = sorted(df2['specialty'].dropna().unique().tolist())

domain_to_i = {d: i for i, d in enumerate(domains)}
time_to_i   = {t: i for i, t in enumerate(time_axis)}
spec_to_i   = {s: i for i, s in enumerate(specialties)}

# Setting colour palette for specialties
palette = px.colors.qualitative.Set3 + px.colors.qualitative.Set2 + px.colors.qualitative.Pastel1
color_map = {s: palette[i % len(palette)] for i, s in enumerate(specialties)}

# Traces/Markers: Specialty Academic, Affects All, Social media

traces = []

# Hover template with reduced hoverlabel styling

HOVERTEMPLATE = (
    "<b>%{customdata.short_title}</b><br>" +
    "Specialty: %{customdata.speciality}<br>" +
    "Time: %{customdata.time_point}<br>" +
    "Domain: %{customdata.domain}<br>" +
    "Impact: %{customdata.impact}" +
    "<extra></extra>"
)

HOVERLABEL = dict(
    bgcolor='rgba(255, 255, 255, 0.9)',
    font=dict(color='black'),
    bordercolor='#FF6B6B'
)

# When click on the data point, get the extract from the reference text
def make_customdata(r: pd.Series) -> dict:
    # Keys aligned to your click-handler expectations
    tp_disp = TIME_TO_DISPLAY.get(safe_str(r.get('time_point')), safe_str(r.get('time_point')))
    return {
        "short_title": safe_str(r.get('incident')),
        "description": safe_str(r.get('description')),
        "time_point":  tp_disp,
        "speciality":  safe_str(r.get('specialty')),
        "domain":      safe_str(r.get('domain')),
        "ref_title":   safe_str(r.get('ref_title')),
        "ref_link":    safe_str(r.get('ref_link')),
        "quote":       safe_str(r.get('quote')),
        "risk_groups": "",               # placeholder - not using this in version 1
        "impact":      float(r.get('impact', 0)),
        "isMultiSource": False           # default; 
    }

# 1) Academic specialty-specific (circles; one trace per specialty)

acad_spec = df2[(~df2['is_social']) & (~df2['is_general'])]

for spec, g in acad_spec.groupby('specialty'):
    x = [domain_to_i[d] + random.uniform(-0.18, 0.18) for d in g['domain']]
    y = [time_to_i[t]   + random.uniform(-0.18, 0.18) for t in g['time_point']]
    z = [spec_to_i[spec]+ random.uniform(-0.18, 0.18) for _ in range(len(g))]
    size = 6 # previously this to integrate impact, can bring back [max(float(v) * 1.5, 5) for v in g['impact']]
    cdata = [make_customdata(r) for _, r in g.iterrows()]

    traces.append(go.Scatter3d(
        x=x, y=y, z=z, mode='markers', name=spec,
        marker=dict(
            size=size,
            color=color_map.get(spec, '#1f77b4'),
            opacity=0.88,
            symbol='circle',
            line=dict(width=0.8, color='rgba(255,255,255,0.9)')
        ),
        customdata=cdata,
        hovertemplate=HOVERTEMPLATE,
        hoverlabel=HOVERLABEL,
        showlegend=True
    ))

# 2) “All specialties” 
acad_general = df2[(~df2['is_social']) & (df2['is_general'])]
if not acad_general.empty:
    x = [domain_to_i[d] + random.uniform(-0.18, 0.18) for d in acad_general['domain']]
    y = [time_to_i[t]   + random.uniform(-0.18, 0.18) for t in acad_general['time_point']]
    z = [spec_to_i[s]   + random.uniform(-0.18, 0.18) for s in acad_general['specialty']]
    size = 4
    cdata = [make_customdata(r) for _, r in acad_general.iterrows()]

    traces.append(go.Scatter3d(
        x=x, y=y, z=z, mode='markers', name='Affects All Specialties',
        marker=dict(
            size=size,
            color='rgba(255,255,255,0.98)',
            opacity=0.88,
            symbol='x',
            line=dict(width=1.0, color='rgba(255,255,255,1)')
        ),
        customdata=cdata,
        hovertemplate=HOVERTEMPLATE,
        hoverlabel=HOVERLABEL,
        showlegend=True
    ))

# 3) Social media (diamonds; warm accent)
social = df2[df2['is_social']]
if not social.empty:
    x = [domain_to_i[d] + random.uniform(-0.18, 0.18) for d in social['domain']]
    y = [time_to_i[t]   + random.uniform(-0.18, 0.18) for t in social['time_point']]
    z = [spec_to_i[s]   + random.uniform(-0.18, 0.18) for s in social['specialty']]
    size = 6
    cdata = [make_customdata(r) for _, r in social.iterrows()]

    traces.append(go.Scatter3d(
        x=x, y=y, z=z, mode='markers', name='Social Media Reports',
        marker=dict(
            size=size,
            color='rgba(255,99,71,0.95)',   # tomato
            opacity=0.88,
            symbol='diamond',
            line=dict(width=1.0, color='rgba(255,255,255,0.95)')
        ),
        customdata=cdata,
        hovertemplate=HOVERTEMPLATE,
        hoverlabel=HOVERLABEL,
        showlegend=True
    ))

# -----------------------------------------------------------------------------
# Layout (white page; BLACK plot panel & scene; cube aspect; legend on LEFT)
# -----------------------------------------------------------------------------
layout = go.Layout(
    title='CIPHER Cube: Patient Harm During Hospital Cyberattacks',
    scene=dict(
        xaxis=dict(
            title='Technical Domain',
            tickvals=list(range(len(domains))),
            ticktext=domains,
            showbackground=True,
            backgroundcolor='black',    # solid black plane
            gridcolor='rgba(255,255,255,0.15)',
            zerolinecolor='rgba(255,255,255,0.25)',
            color='white'
        ),
        yaxis=dict(
            title='Time Point',
            tickvals=list(range(len(time_axis))),
            ticktext=[TIME_TO_DISPLAY.get(t, t) for t in time_axis],
            showbackground=True,
            backgroundcolor='black',    # solid black plane
            gridcolor='rgba(255,255,255,0.15)',
            zerolinecolor='rgba(255,255,255,0.25)',
            color='white'
        ),
        zaxis=dict(
            title='Medical Specialty',
            tickvals=list(range(len(specialties))),
            ticktext=specialties,
            showbackground=True,
            backgroundcolor='black',    # solid black plane
            gridcolor='rgba(255,255,255,0.15)',
            zerolinecolor='rgba(255,255,255,0.25)',
            color='white'
        ),
        bgcolor='black',
        aspectmode='cube',
        dragmode='orbit'
    ),
    paper_bgcolor='black',
    font=dict(color='#111827'),  # page text (outside scene) is dark
    height=820,
    margin=dict(l=0, r=0, t=60, b=0),
    showlegend=True,
    legend=dict(
        orientation='v',
        x=1.02, y=1.0,
        xanchor='left', yanchor='top',
        bgcolor='rgba(0,0,0,0.88)',
        bordercolor='rgba(255,255,255,0.25)',
        borderwidth=1,
        font=dict(color='white')
    )
)

# Build a div + client-side loader that fetches your CSV at runtime
VERSION = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
CSV_URL = f"{CSV_PATH}?v={VERSION}"
SPEC_COLOR_MAP_JSON = json.dumps(color_map)  # dict: {specialty: "#hex", ...}

plot_div = f"""
<div id="cipher-cube" class="plotly-graph-div" style="height:820px; width:100%;"></div>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
// ---- Client-side loader: reproduces your Python-built cube from /data CSV ----
(function() {{
  const CSV_PATH = {CSV_URL!r};

  // Your existing time mapping / ordering
  const TIME_TO_DISPLAY = {{
    "Time 0": "Hour 0",
    "Hour Zero": "Hour 0",
    "First Hour": "Hour 1",
    "First Day": "Day 1",
    "First Week": "Week 1",
    "Week 2": "Week 2",
    "First Month": "Month 1",
    "Unknown": "Unknown"
  }};
  const TIME_ORDER = ["Time 0","Hour Zero","First Hour","First Day","First Week","Week 2","First Month","Unknown"];

  const safe = (v, f='') => (v === undefined || v === null ? f : String(v));
  function normTimePoint(s) {{
    const t = safe(s).trim();
    const low = t.toLowerCase();
    if (["time 0","hour zero","zero","t=0"].includes(low)) return "Time 0";
    if (["first hour","hour 1","1st hour"].includes(low)) return "First Hour";
    if (["firsy day"].includes(low)) return "First Day";
    if (["first day","day 1","1st day"].includes(low)) return "First Day";
    if (["first week","week 1","1st week"].includes(low)) return "First Week";
    if (["week 2","2nd week"].includes(low)) return "Week 2";
    if (["first month","month 1","1st month"].includes(low)) return "First Month";
    if (TIME_TO_DISPLAY[t]) return t;
    return t || "Unknown";
  }}
  function splitSpecialties(s) {{
    const raw = safe(s).trim();
    if (!raw) return ["All"];
    return (raw.replace(/,/g,';').split(';').map(x => x.trim()).filter(Boolean)) || ["All"];
  }}
  function indexer(values) {{
    const uniq = Array.from(new Set(values)).filter(v => v !== "");
    return {{ order: uniq, toIdx: v => uniq.indexOf(v) }};
  }}
  function jitter(n, amt=0.18) {{
    return Array.from({{length:n}}, () => (Math.random()-0.5)*2*amt);
  }}
  function toNum(v, fb=5) {{
    const x = Number(v);
    return Number.isFinite(x) ? x : fb;
  }}

  d3.csv(CSV_PATH).then(raw => {{
    // 1) Normalize & expand multi-specialty rows (mirrors your Python)
    let rows = [];
    raw.forEach(r => {{
      const specialties = splitSpecialties(r["Speciality"]);
      specialties.forEach(sp => {{
        rows.push({{
          incident:    safe(r["Short Title"]),
          description: safe(r["Description of Patient Harm"]),
          time_point:  normTimePoint(r["Time Point"]),
          specialty:   sp || "All",
          domain:      safe(r["Technical Domain"]) || "Unknown",
          ref_title:   safe(r["Reference Title"]),
          ref_link:    safe(r["Reference Link"]),
          quote:       safe(r["Direct Quote"]),
          impact:      toNum(r["Clinical Impact Score"], 5),
          is_social:   (safe(r["Reference Title"]).trim().toLowerCase() === "social media"),
          is_general:  (safe(sp).trim().toLowerCase() === "all")
        }});
      }});
    }});

    // ---- START GROUPING BY SHORT TITLE (collate duplicates into one marker) ----
    const groups = new Map();
    rows.forEach(r => {{
      const key = (r.incident || "").trim();
      if (!key) return;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(r);
    }});

    // Representative rows for plotting + multi-source pages for the modal
    const plotRows = [];
    const multiSourceInfo = {{}};

    groups.forEach((arr, key) => {{
      const rep = arr[0];                  // use first row as marker representative
      plotRows.push({{ ...rep, isMultiSource: arr.length > 1 }});

      multiSourceInfo[key] = {{
        sources: arr.map(r => ({{
          short_title: r.incident,
          description: r.description,
          time_point:  (TIME_TO_DISPLAY[r.time_point] || r.time_point),
          speciality:  r.specialty,
          domain:      r.domain,
          ref_title:   r.ref_title,
          ref_link:    r.ref_link,
          quote:       r.quote,
          impact:      r.impact,
          isMultiSource: true
        }}))
      }};
    }});

    // Expose for the click handler + arrows
    window.multiSourceInfo = multiSourceInfo;
    // ---- END GROUPING BY SHORT TITLE ----

    // 2) Axes & ordering (match your Python ordering)
    const domains = Array.from(new Set(plotRows.map(r => r.domain))).sort();
    const timesInData = Array.from(new Set(plotRows.map(r => r.time_point)));
    const time_axis = [...TIME_ORDER.filter(t => timesInData.includes(t)), ...timesInData.filter(t => !TIME_ORDER.includes(t))];
    const specialties = Array.from(new Set(plotRows.map(r => r.specialty))).sort();

    const domainToI = indexer(domains);
    const timeToI   = indexer(time_axis);
    const specToI   = indexer(specialties);

    // 3) Same three groups / markers as Python build
    const acad_spec    = plotRows.filter(r => !r.is_social && !r.is_general);
    const acad_general = plotRows.filter(r => !r.is_social &&  r.is_general);
    const social       = plotRows.filter(r =>  r.is_social);

    function buildTrace(data, name, symbol, baseSize, colorFn) {{
      const jx = jitter(data.length), jy = jitter(data.length), jz = jitter(data.length);
      const x = data.map((r,i) => domainToI.toIdx(r.domain)   + jx[i]);
      const y = data.map((r,i) => timeToI.toIdx(r.time_point) + jy[i]);
      const z = data.map((r,i) => specToI.toIdx(r.specialty)  + jz[i]);
      const sizes = data.map(_ => baseSize); // fixed sizes to match your current visuals
      const colors= data.map(r => colorFn(r));
      const customdata = data.map(r => ({{
        short_title: r.incident,
        description: r.description,
        time_point:  TIME_TO_DISPLAY[r.time_point] || r.time_point,
        speciality:  r.specialty,
        domain:      r.domain,
        ref_title:   r.ref_title,
        ref_link:    r.ref_link,
        quote:       r.quote,
        impact:      r.impact,
        isMultiSource: !!r.isMultiSource
      }}));
      return {{
        type: 'scatter3d',
        mode: 'markers',
        name,
        x, y, z,
        customdata,
        hovertemplate:
          "<b>%{{customdata.short_title}}</b><br>" +
          "Specialty: %{{customdata.speciality}}<br>" +
          "Time: %{{customdata.time_point}}<br>" +
          "Domain: %{{customdata.domain}}<br>" +
          "Impact: %{{customdata.impact}}<extra></extra>",
        hoverlabel: {{
          bgcolor: 'rgba(255,255,255,0.9)',
          font: {{color: 'black'}},
          bordercolor: '#FF6B6B'
        }},
        marker: {{
          size: sizes,
          symbol: symbol,
          color: colors,
          opacity: 0.88,
          line: {{width: 0.8, color: 'rgba(255,255,255,0.9)'}}
        }}
      }};
    }}

    // Specialty color map injected from Python so colours match previous build
    const SPEC_COLOR_MAP = {SPEC_COLOR_MAP_JSON};
    const specColors = new Map(Object.entries(SPEC_COLOR_MAP));

    const traces = [];
    // Build one trace per specialty from the academic, specialty-specific rows
    const bySpec = new Map();
    acad_spec.forEach(r => {{
      if (!bySpec.has(r.specialty)) bySpec.set(r.specialty, []);
      bySpec.get(r.specialty).push(r);
    }});

    // Add per-specialty traces so each shows in the legend with its color
    Array.from(bySpec.keys()).sort().forEach(specName => {{
      const rowsForSpec = bySpec.get(specName);
      traces.push(
        buildTrace(
          rowsForSpec,
          specName,            // legend label = specialty
          "circle",
          10,                  // marker size (tweak if you like)
          _ => specColors.get(specName) || "#1f77b4"
        )
      );
    }});

    // Keep these two as single traces
    if (acad_general.length) {{
      traces.push(
        buildTrace(
          acad_general,
          "Affects All Specialties",
          "x",
          8,
          _ => "rgba(255,255,255,0.98)"
        )
      );
    }}
    if (social.length) {{
      traces.push(
        buildTrace(
          social,
          "Social Media Reports",
          "diamond",
          9,
          _ => "rgba(255,99,71,0.95)"
        )
      );
    }}

    // Layout: mirrors your Python layout exactly
    const layout = {{
      title:'CIPHER Cube: Patient Harm During Hospital Cyberattacks',
      scene:{{
        xaxis:{{ title:'Technical Domain', tickvals: domains.map((_,i)=>i), ticktext: domains,
                 showbackground:true, backgroundcolor:'black', gridcolor:'rgba(255,255,255,0.15)',
                 zerolinecolor:'rgba(255,255,255,0.25)', color:'white' }},
        yaxis:{{ title:'Time Point', tickvals: time_axis.map((_,i)=>i), ticktext: time_axis.map(t => TIME_TO_DISPLAY[t] || t),
                 showbackground:true, backgroundcolor:'black', gridcolor:'rgba(255,255,255,0.15)',
                 zerolinecolor:'rgba(255,255,255,0.25)', color:'white' }},
        zaxis:{{ title:'Medical Specialty', tickvals: specialties.map((_,i)=>i), ticktext: specialties,
                 showbackground:true, backgroundcolor:'black', gridcolor:'rgba(255,255,255,0.15)',
                 zerolinecolor:'rgba(255,255,255,0.25)', color:'white' }},
        bgcolor:'black', aspectmode:'cube', dragmode:'orbit'
      }},
      paper_bgcolor:'black',
      font:{{ color:'#111827' }},
      height:820,
      margin:{{ l:0, r:0, t:60, b:0 }},
      showlegend:true,
      legend:{{
        orientation:'v', x:1.02, y:1.0, xanchor:'left', yanchor:'top',
        bgcolor:'rgba(0,0,0,0.88)', bordercolor:'rgba(255,255,255,0.25)',
        borderwidth:1, font:{{color:'white'}}
      }}
    }};

    Plotly.newPlot('cipher-cube', traces, layout, {{responsive:true}});
  }}).catch(err => {{
    console.error('CSV load error:', err);
    const el = document.getElementById('cipher-cube');
    if (el) el.innerHTML = '<p style="padding:1rem;color:#b91c1c">Error loading data. Check the CSV path/filename and column names.</p>';
  }});
}})();
</script>
"""

# -----------------------------------------------------------------------------

# FORMATTING FOR PAGE
# Page template (white page; restores header + 3 info cards; includes modal & JS)
# Plot panel is pure black so the white scene blends seamlessly.
# Edits here for Io Page etc

HTML_PAGE = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>CIPHER Cube · Patient Harm During Hospital Cyberattacks</title>
  <meta name="description" content="Interactive 3D map of documented patient harms during hospital cyberattacks, combining academic literature and social media reports."/>

  <!-- Bootstrap for the modal (GitHub Pages safe) -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css"/>

  <style>
    :root {{
      --ink: #111827;
      --muted: #6b7280;
      --panel: #0f172a;     /* navy panels for info cards */
      --panel-ink: #e5e7eb;
      --accent: #2563eb;
    }}
    html, body {{
      margin: 0; padding: 0;
      background: #ffffff;
      color: var(--ink);
      font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";
      line-height: 1.6;
    }}
    .wrap {{ max-width: 1120px; margin: 0 auto; padding: 24px; }}
    .title {{ font-weight: 800; font-size: clamp(28px,5vw,42px); letter-spacing: -0.02em; }}
    .subtitle {{ color: var(--muted); max-width: 72ch; }}
    .badge-lite {{ display:inline-block; padding: 6px 10px; border-radius: 999px; background:#eef2ff; color:#3730a3; font-size:12px; border:1px solid #c7d2fe; }}

    .panel {{
      background: var(--panel);
      color: var(--panel-ink);
      border-radius: 16px;
      border: 1px solid rgba(255,255,255,0.08);
      padding: 18px;
      box-shadow: 0 10px 24px rgba(0,0,0,0.15);
    }}

    /* PURE BLACK panel for the plot */
    .panel-plot {{
      background: #000000;
      color: #e5e7eb; /* labels above the plot */
      border: 1px solid rgba(255,255,255,0.10);
    }}

    .legend-note {{ color: #cbd5e1; font-size: 14px; }}
    .grid {{ display: grid; gap: 16px; grid-template-columns: 1fr; }}
    @media(min-width: 900px) {{ .grid-3 {{ grid-template-columns: 1fr 1fr 1fr; }} }}

    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}

    /* Modal polish */
    .modal-border-multi {{ border-left: 6px solid #f59e0b; }}
    .modal-body p {{ margin-bottom: 0.5rem; }}
  </style>

</head>
<body>
  <div class="wrap">
    <header style="margin: 24px 0 18px; text-align:center">
      <span class="badge-lite">CIPHER Platform</span>
      <h1 class="title" style="margin:10px 0 6px;">The CIPHER Cube Models</h1>
      <p class="text-sm mb-4">
        <b>CIPHER</b> was built to model <b>C</b>yberattack <b>I</b>mpacts, <b>P</b>atient <b>H</b>arms and effective <b>E</b>mergency <b>R</b>esponse during IT downtime at healthcare organisations.
        To do this, our research collected examples of patient harms occuring during healthcare cyberattacks from diverse data sources, to form one combined
        <b>'CIPHER database' </b>.
        The CIPHER models on this page draw from our two key datasets described on the <a href="https://www.thecipherplatform.com">project website</a>, consisting of <b>(1) The "Hospital Attacks"</b> dataset (a systematic review of
        global papers reporting healthcare cyberattacks), and <b>(2) The "Patient Harms"</b> dataset (extracted through data mining social media posts). 
        From these two sources we created the full <b>CIPHER dataset</b>, available in the data folder in the GitHub Repo,
        which provides over <b>300 patient-level harms</b> reported to have occured following a healthcare cyberattack.
      </p>
      <p class="text-sm mb-4">
        Below you will find the <b>interactive "Hospital at Ransom" cube</b>, which is a demo model built from the CIPHER database, developed for a hypothetical hospital context.
        For these models to be effective for local hospital context, users would need to update the underlying data for the likely clinical impact in their hospitals. 
        For instance, we have assigned 'Clinical Impact' scores to each patient safety incident in the CIPHER dataset, based on the likely effect in our hypothetical hospital (e.g. this hospital
        has a heavy reliance on e-Prescribing in the ER, thus loss of digital drug release would have a high degree of impact). By downloading the underlying datasets
        and contextualising impact for local circumstances, users can utilise the database of cyberattack-induced patient safety incidents and tailor the model to their environment.
      </p>
      <p class="text-sm mb-4">
        The demo model provides an approach for <b>minimising clinical surprise</b> during
        hospital cyberattacks, by predicting potential adverse events from hour 1 of the cyberattack, to day 28. 
        Users can filted the model to examine harms relevant to <b>specifical technical domains</b> (e.g. safety incidents related to loss of the laboratory systems) or <b>specific clinical areas</b> (e.g. harms likely to occur on paediatrics wards).
        The full models on the <a href="https://www.thecipherplatform.com">project website</a> can also be manipulated to plot the 'Clinical Impact' scores on the Y axis,
        thus providing time-series predictions of potential clinical harm over time (from 24 hours to Day 28).
        By showcasing these diverse events, assigning clinical impact scores and identifying
        the at-risk patient groups and necessary medical interventions, these models can be used to enhance Cyberattack incident response processes to protect patient care.
      </p>
      <p class="text-sm mb-4">
        <b>Click on each <u>data point</u> below to view an <u>information pane</u> detailing the safety incident, and links to underlying source material</b> 
      </p>
    </header>

    <section class="panel panel-plot">
      <h3 style="margin-top:0; color:#e5e7eb;">The "Hospital At Ransom" Cube</h3>
      <p class="legend-note">
      The 3D visualisation maps document patient harms during hospital cyberattacks. 
      Each data point on the 3D visulisation represents a specific patient safety incident, which you can <b>hover</b> over for brief information, 
      or <b><u>click on the data point</b></u> for the full details and background sources.
      </p>      
      <p class="legend-note">• <b>● Circles</b>: Academic (specialty-specific) &nbsp; • <b>✕ X</b>: Affects all specialties &nbsp; • <b>♦ Diamonds</b>: Social media reports</p>
      <div style="margin-top:10px;">
        {plot_div}
      </div>
    </section>

    <section class="grid grid-3" style="margin-top:16px;">
      <div class="panel">
        <h4>How to use</h4>
        <p>Rotate, pan, zoom. Hover for details. Click a point for a full source panel; multi-source items provide next/previous navigation.</p>
      </div>
      <div class="panel">
        <h4>What’s plotted</h4>
        <p><b>Domain</b> (X) · <b>Time Point</b> (Y) · <b>Specialty</b> (Z). Markers are sized by reported Clinical Impact Score and jittered to reduce overlap.</p>
      </div>
      <div class="panel">
        <h4>Data sources</h4>
        <p>Peer-reviewed literature and staff/patient reports from social platforms. Interpretation is for situational awareness, not clinical guidance.</p>
      </div>
    </section>

    <footer style="color:#6b7280; font-size:14px; margin:32px 0 64px;">
      © {pd.Timestamp.now().year} · Built with Python & Plotly · Static HTML (GitHub Pages)
    </footer>
  </div>

  <!-- Modal skeleton that your click-handler uses -->
  <div class="modal fade" id="infoPanel" tabindex="-1" role="dialog" aria-labelledby="infoPanelTitle" aria-hidden="true">
    <div class="modal-dialog modal-lg modal-dialog-scrollable" role="document">
      <div class="modal-content" id="infoPanelContent">
        <div class="modal-header">
          <h5 class="modal-title" id="infoPanelTitle">Incident</h5>
          <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        </div>
        <div class="modal-body" id="infoPanelBody">
          <!-- Populated on click -->
        </div>
        <div class="modal-footer" id="sourceNavigation" style="display:none; width:100%; justify-content:space-between;">
          <button type="button" class="btn btn-outline-secondary" id="prevSource">◀ Previous</button>
          <button type="button" class="btn btn-outline-secondary" id="nextSource">Next ▶</button>
        </div>
      </div>
    </div>
  </div>

  <!-- jQuery + Bootstrap JS (for modal) -->
  <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>

  <!-- Hook up hover cursor + click→modal behavior -->
  <script>
    // Optional: provide multiSourceInfo structure here if available from your build
    window.multiSourceInfo = window.multiSourceInfo || {{}};

    // Debounce helper (used by your snippet)
    function debounce(fn, delay) {{
      let t = null;
      return function() {{
        const args = arguments, ctx = this;
        clearTimeout(t);
        t = setTimeout(function() {{ fn.apply(ctx, args); }}, delay);
      }};
    }}

    // Fallback single-source renderer (used if your site-specific function isn't injected)
    function createSingleSourceModalContent(cd) {{
      const safe = (v) => (v === undefined || v === null) ? '' : String(v);
      const linkHtml = cd.ref_link 
        ? `<p><b>Reference:</b> <a href="${{cd.ref_link}}" target="_blank" rel="noopener">${{safe(cd.ref_title) || 'Source'}}</a></p>`
        : `<p><b>Reference:</b> ${{safe(cd.ref_title)}}</p>`;
      const quoteHtml = cd.quote ? `<blockquote class="blockquote" style="font-size:0.95rem;">${{cd.quote}}</blockquote>` : '';
      return `
        <p><b>Specialty:</b> ${{safe(cd.speciality)}} &nbsp; | &nbsp; <b>Time:</b> ${{safe(cd.time_point)}} &nbsp; | &nbsp; <b>Domain:</b> ${{safe(cd.domain)}} &nbsp; | &nbsp; <b>Impact:</b> ${{safe(cd.impact)}}</p>
        <p>${{safe(cd.description)}}</p>
        ${{linkHtml}}
        ${{quoteHtml}}
      `;
    }}

    // Optional multi-source renderer stub (page can override with richer logic)
    function displayMultiSourcePanel(shortTitle, idx) {{
      const sources = (window.multiSourceInfo[shortTitle] || {{}}).sources || [];
      const s = sources[idx] || null;
      const body = document.getElementById('infoPanelBody');
      if (!s) {{ body.innerHTML = '<p>No source details available.</p>'; return; }}
      body.innerHTML = createSingleSourceModalContent(s);
    }}

    // State for multi-source nav
    window.currentSourceIndex = 0;
    window.currentSources = [];

    // Attach handlers after Plotly has rendered (local loads can be too fast)
    (function attachHandlersWhenReady() {{
      var plot = document.getElementById('cipher-cube');

      // Wait until the div exists AND Plotly has populated layout/data
      if (!plot || !(plot.data || plot._fullData)) {{
        setTimeout(attachHandlersWhenReady, 60);
        return;
      }}

      // Clear any previous bindings (hot reloads)
      if (plot.removeAllListeners) {{
        plot.removeAllListeners('plotly_hover');
        plot.removeAllListeners('plotly_unhover');
        plot.removeAllListeners('plotly_click');
      }}

      // Cursor polish on hover
      plot.on('plotly_hover', debounce(function () {{
        document.body.style.cursor = 'pointer';
      }}, 30));

      plot.on('plotly_unhover', debounce(function () {{
        document.body.style.cursor = 'default';
      }}, 50));

      // CLICK -> open modal with either single- or multi-source view
      plot.on('plotly_click', function (data) {{
        if (!data || !data.points || !data.points[0]) return;

        var pointData = data.points[0].customdata || {{}};

        window.currentSourceIndex = 0;
        window.currentSources = [];

        var isMultiSource = (pointData.isMultiSource === true || pointData.isMultiSource === "true");
        var shortTitle = pointData.short_title;

        var titleEl = document.getElementById('infoPanelTitle');
        if (titleEl) titleEl.textContent = shortTitle || 'Incident';

        var modalContent = document.getElementById('infoPanelContent');
        if (modalContent) {{
          if (isMultiSource && window.multiSourceInfo && window.multiSourceInfo[shortTitle]) {{
            modalContent.classList.add('modal-border-multi');
          }} else {{
            modalContent.classList.remove('modal-border-multi');
          }}
        }}

        var sourceNav = document.getElementById('sourceNavigation');

        if (isMultiSource && window.multiSourceInfo && window.multiSourceInfo[shortTitle]) {{
          window.currentSources = window.multiSourceInfo[shortTitle].sources || [];
          displayMultiSourcePanel(shortTitle, window.currentSourceIndex);
          if (sourceNav) sourceNav.style.display = 'flex';
        }} else {{
          if (sourceNav) sourceNav.style.display = 'none';
          var bodyEl = document.getElementById('infoPanelBody');
          if (bodyEl) bodyEl.innerHTML = createSingleSourceModalContent(pointData);
        }}

        // Show the Bootstrap modal
        if (window.jQuery && typeof jQuery.fn.modal === 'function') {{
          jQuery('#infoPanel').modal('show');
        }} else {{
          // Fallback if Bootstrap JS failed to load
          var m = document.getElementById('infoPanel');
          if (m) m.style.display = 'block';
        }}
      }});
    }})();

    // Nav buttons
    const prevSourceBtn = document.getElementById('prevSource');
    if (prevSourceBtn) {{
      prevSourceBtn.addEventListener('click', function () {{
        if (window.currentSourceIndex > 0) {{
          window.currentSourceIndex--;
          displayMultiSourcePanel(document.getElementById('infoPanelTitle').textContent, window.currentSourceIndex);
        }}
      }});
    }}
    const nextSourceBtn = document.getElementById('nextSource');
    if (nextSourceBtn) {{
      nextSourceBtn.addEventListener('click', function () {{
        if (window.currentSources && window.currentSourceIndex < window.currentSources.length - 1) {{
          window.currentSourceIndex++;
          displayMultiSourcePanel(document.getElementById('infoPanelTitle').textContent, window.currentSourceIndex);
        }}
      }});
    }}
  </script>
</body>
</html>
"""

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(HTML_PAGE)

print(f"Generated {OUTPUT_HTML} (open locally or push to GitHub Pages).")
