
export interface ExplodedLayer {
  layerNumber: number;
  partName: string;
  materialSpec: string;
  thicknessMm: string;
  toleranceMm: string;
  functionRole: string;
  visualColor: string;
  explodedOffsetPx?: number;
}

export interface ExplodedProduct {
  id: number;
  number: number;
  name: string;
  category: 'water' | 'energy' | 'biomaterials' | 'packaging' | 'sensors' | 'smart_fabrics';
  drawingCode: string; // pl. "ISO-128-FV-076"
  materials: string[];
  mechanism: string;
  layers: ExplodedLayer[];
  assemblyInstructions: string[];
  unitCostHuf: number;
  targetPriceHuf: number;
}

export interface AIDiagramResponse {
  productNumber: number;
  productName: string;
  cadDrawingTitle: string;
  explodedLayers: ExplodedLayer[];
import express from 'express';
import { GoogleGenAI } from '@google/genai';

const app = express();
app.use(express.json());

const ai = new GoogleGenAI(); // GOOGLE_GENAI_API_KEY a környezeti változókból

// AI Műszaki Robbantott Rajz & Diagram Generátor Végpont
app.post('/api/generate-exploded-diagram', async (req, res) => {
  try {
    const { productNumber, productName, materials, mechanism, customStyle } = req.body;

    const systemInstruction = `
Te egy vezető ISO 128 gépész- és biomérnök tervező vagy, aki robbantott műszaki rajzokat (Exploded Engineering Blueprint) tervez.
Készíts precíz robbantott réteg-lebontást és egy közvetlenül megjeleníthető, érvényes SVG műszaki rajzot!

Kimeneti JSON séma:
{
  "productNumber": number,
  "productName": string,
  "cadDrawingTitle": string,
  "explodedLayers": [
    {
      "layerNumber": number,
      "partName": string,
      "materialSpec": string,
      "thicknessMm": string,
      "toleranceMm": string,
      "functionRole": string,
      "visualColor": string
    }
  ],
  "operatingMechanism": string,
  "fluidOrThermalFlow": string,
  "fastenersAndAssembly": string,
  "svgDiagramCode": string, // Teljes <svg viewBox="0 0 800 600">...</svg> mérnöki rajz sötétkék blueprint háttérrel (#0f172a), cián vonalakkal (#38bdf8), szaggatott robbantási tengellyel (dasharray) és feliratokkal
  "engineerNotes": string
}`;

    const prompt = `Készíts robbantott műszaki rajzot és diagramot az alábbi termékhez:
- Sorszám: #${productNumber}
- Név: ${productName}
- Alapanyagok: ${Array.isArray(materials) ? materials.join(', ') : materials}
- Működési mechanizmus: ${mechanism}
- Stílus: ${customStyle || 'ISO 128 CAD blueprint, robbantott rétegekkel és méretezéssel'}`;

    const response = await ai.models.generateContent({
      model: 'gemini-3.8-flash',
      contents: prompt,
      config: {
        systemInstruction,
        responseMimeType: 'application/json',
        temperature: 0.35,
      },
    });

    const parsedData = JSON.parse(response.text || '{}');
    res.json(parsedData);
  } catch (err: any) {
    console.error('Hiba a robbantott diagram generálásakor:', err);
    res.status(500).json({ error: 'AI generálási hiba', details: err?.message });
  }
});
import React, { useState } from 'react';
import { ExplodedProduct, AIDiagramResponse } from '../types/explodedDiagram';

interface Props {
  products: ExplodedProduct[];
}

export const ExplodedGallery100View: React.FC<Props> = ({ products }) => {
  const [selectedProduct, setSelectedProduct] = useState<ExplodedProduct>(products[0]);
  const [explodedDistance, setExplodedDistance] = useState<number>(65); // Szétszerelési távolság (px)
  const [aiDiagram, setAiDiagram] = useState<AIDiagramResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Gemini API hívás a kiválasztott termékre
  const handleGenerateAiDiagram = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/generate-exploded-diagram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          productNumber: selectedProduct.number,
          productName: selectedProduct.name,
          materials: selectedProduct.materials,
          mechanism: selectedProduct.mechanism,
        }),
      });
      const data = await res.json();
      setAiDiagram(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6 bg-slate-950 text-slate-100">
      {/* 1. Bal oldali termékválasztó lista (1-100) */}
      <div className="h-[800px] overflow-y-auto space-y-2 pr-2 border-r border-slate-800">
        <h2 className="text-xl font-bold text-cyan-400">100 Termék Portfólió</h2>
        {products.map((p) => (
          <button
            key={p.id}
            onClick={() => { setSelectedProduct(p); setAiDiagram(null); }}
            className={`w-full text-left p-3 rounded-lg border transition ${
              selectedProduct.id === p.id 
                ? 'bg-cyan-950/60 border-cyan-500 text-cyan-300' 
                : 'bg-slate-900 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="text-xs text-cyan-400 font-mono">#{p.number} • {p.drawingCode}</div>
            <div className="font-semibold text-sm">{p.name}</div>
          </button>
        ))}
      </div>

      {/* 2. Középső Interaktív SVG Rajzasztal (Robbantott rétegekkel) */}
      <div className="lg:col-span-2 flex flex-col gap-4">
        {/* Vezérlősáv */}
        <div className="flex items-center justify-between bg-slate-900 p-4 rounded-xl border border-slate-800">
          <div>
            <h3 className="font-bold text-lg text-white">{selectedProduct.name}</h3>
            <span className="text-xs text-slate-400 font-mono">{selectedProduct.drawingCode}</span>
          </div>

          <div className="flex items-center gap-4">
            <label className="text-xs text-slate-400">Robbantási távolság:</label>
            <input
              type="range"
              min="0"
              max="150"
              value={explodedDistance}
              onChange={(e) => setExplodedDistance(Number(e.target.value))}
              className="accent-cyan-400"
            />
            <button
              onClick={handleGenerateAiDiagram}
              disabled={isLoading}
              className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-lg text-sm font-semibold hover:from-cyan-500 hover:to-blue-500 transition shadow"
            >
              {isLoading ? 'AI Tervezés...' : '✨ Gemini AI Műszaki Rajz'}
            </button>
          </div>
        </div>

        {/* CAD Canvas */}
        <div className="relative h-[600px] bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden flex items-center justify-center">
          {aiDiagram?.svgDiagramCode ? (
            <div 
              className="w-full h-full p-4 flex items-center justify-center"
              dangerouslySetInnerHTML={{ __html: aiDiagram.svgDiagramCode }} 
            />
          ) : (
            /* Parametrikus réteg-renderelő */
            <svg viewBox="0 0 800 600" className="w-full h-full select-none">
              <defs>
                <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="0.8" />
                </pattern>
              </defs>
              <rect width="800" height="600" fill="#0b1329" />
              <rect width="800" height="600" fill="url(#grid)" />

              {/* Szaggatott robbantási tengely */}
              <line x1="400" y1="50" x2="400" y2="550" stroke="#0284c7" strokeWidth="1.5" strokeDasharray="8 4" opacity="0.6" />

              {/* Dinamikusan eltolt robbantott rétegek */}
              {selectedProduct.layers.map((layer, idx) => {
                const total = selectedProduct.layers.length;
                const offset = (idx - total / 2) * explodedDistance;
                const y = 300 + offset;

                return (
                  <g key={layer.layerNumber} className="transition-all duration-300 ease-out">
                    <rect
                      x="250"
                      y={y - 18}
                      width="300"
                      height="36"
                      rx="6"
                      fill={layer.visualColor || '#0369a1'}
                      stroke="#38bdf8"
                      strokeWidth="1.5"
                      opacity="0.85"
                    />
                    <text x="400" y={y + 5} fill="#ffffff" fontSize="13" textAnchor="middle" fontWeight="bold">
                      [{layer.layerNumber}] {layer.partName} ({layer.thicknessMm})
                    </text>
                    {/* Vezetővonal és felirat */}
                    <line x1="550" y1={y} x2="630" y2={y} stroke="#38bdf8" strokeWidth="1" strokeDasharray="3 3" />
                    <text x="635" y={y + 4} fill="#94a3b8" fontSize="11" fontFamily="monospace">
                      {layer.materialSpec}
                    </text>
                  </g>
                );
              })}
            </svg>
          )}
        </div>
      </div>
    </div>
  );
};
  operatingMechanism: string;
  fluidOrThermalFlow: string;
  fastenersAndAssembly: string;
  svgDiagramCode: string; // ISO 128 CAD kompatibilis SVG kód
  engineerNotes: string;
}
import os
import json
import requests
from google import genai
from google.genai import types

class ProductExplodedBlueprintEngine:
    """100 Termék Robbantott CAD & Műszaki Rajz Generátor Motor"""

    def __init__(self, api_key: str = None):
        self.client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))

    def generate_blueprint_spec(self, product_no: int, name: str, materials: list, mechanism: str) -> dict:
        prompt = f"""
Készíts ISO 128 szabvány szerinti robbantott műszaki rajzot:
- Termék #{product_no}: {name}
- Alapanyagok: {', '.join(materials)}
- Működési mechanizmus: {mechanism}
"""
        response = self.client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="Te egy vezető gépészmérnök vagy. Válaszolj szigorúan JSON-ben {productNumber, cadTitle, layers: [{name, material, thickness, role}], svgDiagramCode}.",
                response_mime_type="application/json",
                temperature=0.3
            )
        )
        return json.loads(response.text)

    def export_svg(self, blueprint_data: dict, output_filepath: str):
        svg_code = blueprint_data.get("svgDiagramCode", "")
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(svg_code)
        print(f"✅ Mentve: {output_filepath}")

# Használati példa:
if __name__ == "__main__":
    engine = ProductExplodedBlueprintEngine()
    data = engine.generate_blueprint_spec(
        product_no=76,
        name="MycoComposite Akusztikai Panel",
        materials=["Gombafonal micélium", "Mezőgazdasági biomassza", "Természetes viasz bevonat"],
        mechanism="Porózus szálmátrix akusztikai abszorpcióval és mikrogomba-kötéssel"
    )
    engine.export_svg(data, "mycocomposite_exploded.svg")
