/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { Terminal, FileCode, CheckCircle2 } from 'lucide-react';

export default function App() {
  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-200 flex flex-col items-center justify-center p-6 font-sans">
      <div className="max-w-2xl w-full bg-neutral-900 border border-neutral-800 rounded-xl shadow-2xl overflow-hidden">
        <div className="p-8">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg">
              <FileCode className="w-6 h-6" />
            </div>
            <h1 className="text-2xl font-medium text-white">Streamlit App Generated</h1>
          </div>
          
          <p className="text-neutral-400 mb-6 leading-relaxed">
            I have successfully generated your complete Python/Streamlit Movie Explorer application exactly as requested, strictly following your constraints (No HTML, CSS, or JS).
          </p>

          <div className="bg-black/50 rounded-lg p-5 border border-neutral-800 mb-8 font-mono text-sm">
            <h3 className="text-neutral-500 mb-3 uppercase tracking-wider text-xs font-semibold">Generated Files</h3>
            <ul className="space-y-3 text-neutral-300">
              <li className="flex items-center"><CheckCircle2 className="w-4 h-4 mr-2 text-green-500"/> <span className="text-blue-400 mr-2">app.py</span> (Main Streamlit App)</li>
              <li className="flex items-center"><CheckCircle2 className="w-4 h-4 mr-2 text-green-500"/> <span className="text-green-400 mr-2">requirements.txt</span> (Dependencies)</li>
              <li className="flex items-center"><CheckCircle2 className="w-4 h-4 mr-2 text-green-500"/> <span className="text-yellow-400 mr-2">.env.example</span> (Environment config)</li>
            </ul>
          </div>

          <div className="space-y-4">
            <h3 className="text-white font-medium text-lg">How to run your app locally:</h3>
            
            <div className="bg-neutral-950 rounded-md p-5 border border-neutral-800 font-mono text-sm text-neutral-300 overflow-x-auto leading-loose">
              <div className="text-neutral-500"># 1. Export this project (top-right menu) and extract the ZIP.</div>
              <div className="text-neutral-500"># 2. Create a virtual environment</div>
              <div>python -m venv venv</div>
              <div>source venv/bin/activate  <span className="text-neutral-600"># On Windows: venv\Scripts\activate</span></div>
              <br/>
              <div className="text-neutral-500"># 3. Install dependencies</div>
              <div>pip install -r requirements.txt</div>
              <br/>
              <div className="text-neutral-500"># 4. Add your TMDB API key</div>
              <div>cp .env.example .env</div>
              <div className="text-neutral-500"># (Open .env and replace with your actual TMDB_API_KEY)</div>
              <br/>
              <div className="text-neutral-500"># 5. Run the Streamlit app</div>
              <div className="text-blue-400">streamlit run app.py</div>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-950 px-8 py-4 border-t border-neutral-800 flex justify-between items-center text-sm text-neutral-500">
          <span>AI Studio Preview Environment</span>
          <span className="flex items-center"><Terminal className="w-4 h-4 mr-1"/> Node.js React Runtime</span>
        </div>
      </div>
    </div>
  );
}
