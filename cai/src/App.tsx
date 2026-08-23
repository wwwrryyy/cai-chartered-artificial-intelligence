import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import ASCIIText from './components/ASCIIText';
import OptionWheel from './components/OptionWheel';

const ROUTES = [
  { name: 'Dashboard', path: '/' },
  { name: 'Upload', path: '/upload' },
  { name: 'Review', path: '/review' },
  { name: 'Deductions', path: '/deductions' }
];

function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  
  const activeIndex = Math.max(ROUTES.findIndex(r => r.path === location.pathname), 0);

  const handleNavigate = (index: number) => {
    navigate(ROUTES[index].path);
  };

  return (
    <div className="relative w-full h-screen bg-black overflow-hidden text-white font-sans selection:bg-[var(--color-beige)]/30">
      <div className="absolute inset-0 z-0">
        <ASCIIText />
      </div>

      <div className="absolute inset-0 z-10 pointer-events-none">
        <div className="pointer-events-auto h-full">
          <OptionWheel 
            items={ROUTES.map(r => r.name)} 
            activeIndex={activeIndex} 
            onSelect={handleNavigate} 
          />
        </div>
      </div>

      <div className="absolute right-12 top-0 bottom-0 w-full md:w-[calc(100%-26rem)] z-20 p-6 md:p-8 lg:p-12 overflow-y-auto">
        <div className="ios-liquid-glass w-full min-h-full rounded-[2rem] p-8 md:p-12 flex flex-col shadow-2xl relative overflow-hidden">
          <div className="absolute -top-40 -right-40 w-96 h-96 bg-[var(--color-beige)]/10 rounded-full blur-3xl pointer-events-none"></div>
          
          <div className="relative z-10 h-full flex flex-col">
            <Routes>
              <Route path="/" element={<DashboardView />} />
              <Route path="/upload" element={<UploadView />} />
              <Route path="/review" element={<ReviewView />} />
              <Route path="/deductions" element={<DeductionsView />} />
            </Routes>
          </div>
        </div>
      </div>
    </div>
  );
}

function DashboardView() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch('http://localhost:8001/api/dashboard')
      .then(res => res.json())
      .then(setData)
      .catch(console.error);
  }, []);

  return (
    <div className="flex flex-col h-full animate-fade-in flex-1">
      <h1 className="text-4xl md:text-5xl font-light mb-2 tracking-tight text-[var(--color-beige)]">Dashboard</h1>
      <p className="text-[var(--color-slate)] mb-12 text-lg">CAI Intelligence Overview</p>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {[
          { label: 'Total Income', value: data ? `₹${data.total_income.toLocaleString()}` : '...' },
          { label: 'Tax Liability', value: data ? `₹${data.tax_liability.toLocaleString()}` : '...' },
          { label: 'Deductions Found', value: data ? `₹${data.deductions_found.toLocaleString()}` : '...' }
        ].map(metric => (
          <div key={metric.label} className="ios-liquid-glass p-6 rounded-2xl flex flex-col group hover:bg-white/5 transition-colors">
            <span className="text-xs font-semibold text-[var(--color-slate)] uppercase tracking-[0.2em] mb-3">{metric.label}</span>
            <span className="text-3xl font-medium tracking-tight text-white group-hover:text-[var(--color-beige)] transition-colors">{metric.value}</span>
          </div>
        ))}
      </div>
      
      {data && data.tax_result && data.tax_result.recommended_regime && (
        <div className="ios-liquid-glass p-8 rounded-2xl flex-1 flex flex-col border border-[var(--color-beige)]/20 relative overflow-hidden group">
          <h2 className="text-xl text-[var(--color-beige)] mb-4">Regime Recommendation: {data.tax_result.recommended_regime.toUpperCase()}</h2>
          <div className="grid grid-cols-2 gap-8">
            <div>
              <p className="text-[var(--color-slate)] text-sm mb-1 uppercase tracking-wider">Old Regime Tax</p>
              <p className="text-2xl font-mono">₹{data.tax_result.old_regime?.final_tax.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-[var(--color-slate)] text-sm mb-1 uppercase tracking-wider">New Regime Tax</p>
              <p className="text-2xl font-mono">₹{data.tax_result.new_regime?.final_tax.toLocaleString()}</p>
            </div>
          </div>
          <div className="mt-8 text-lg">
            Projected Savings: <span className="text-[var(--color-beige)] font-bold">₹{data.tax_result.savings.toLocaleString()}</span>
          </div>
        </div>
      )}
      
      {(!data || !data.tax_result || !data.tax_result.recommended_regime) && (
        <div className="ios-liquid-glass p-8 rounded-2xl flex-1 flex flex-col items-center justify-center border border-white/5 relative overflow-hidden group">
           <p className="text-[var(--color-slate)] font-mono text-xs tracking-[0.3em] uppercase relative z-10">Waiting for data extraction</p>
        </div>
      )}
    </div>
  );
}

function UploadView() {
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [textInput, setTextInput] = useState('');
  const [files, setFiles] = useState<string[]>([]);

  const fetchFiles = () => {
    fetch('http://localhost:8001/api/dashboard')
      .then(res => res.json())
      .then(data => {
        if (data && data.files) setFiles(data.files);
      })
      .catch(console.error);
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setUploading(true);
    setMessage('Extracting and Analysing with Qwen...');
    const formData = new FormData();
    for (let i = 0; i < e.target.files.length; i++) { formData.append('files', e.target.files[i]); }
    try {
      const res = await fetch('http://localhost:8001/api/upload', { method: 'POST', body: formData });
      const data = await res.json();
      setMessage(`Success! Extracted data and found ${data.deductions_count} deductions.`);
      fetchFiles();
    } catch (err) {
      console.error(err);
      setMessage('Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleTextSubmit = async () => {
    if (!textInput.trim()) return;
    setUploading(true);
    setMessage('Analyzing text with CAI...');
    
    const file = new File([textInput], "notes.txt", { type: "text/plain" });
    const formData = new FormData();
    formData.append('files', file);

    try {
      const res = await fetch('http://localhost:8001/api/upload', { method: 'POST', body: formData });
      const data = await res.json();
      setMessage(`Success! Extracted data and found ${data.deductions_count} deductions.`);
      setTextInput('');
      fetchFiles();
    } catch (err) {
      console.error(err);
      setMessage('Analysis failed.');
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="flex flex-col h-full animate-fade-in flex-1">
      <h1 className="text-4xl md:text-5xl font-light mb-2 tracking-tight text-[var(--color-beige)]">Upload & Analyze</h1>
      <p className="text-[var(--color-slate)] mb-8 text-lg">Provide documents or explain your finances to CAI</p>
      
      <div className="flex gap-6 flex-1 mb-8">
        <div className="relative ios-liquid-glass p-12 rounded-2xl flex-1 flex flex-col items-center justify-center border-2 border-dashed border-white/10 hover:border-[var(--color-beige)]/40 hover:bg-white/[0.02] transition-all cursor-pointer group">
          <input type="file" multiple onChange={handleFileChange} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" disabled={uploading} />
          <div className="w-24 h-24 rounded-full ios-liquid-glass flex items-center justify-center mb-8 group-hover:scale-110 transition-transform shadow-[0_0_30px_rgba(196,168,130,0.1)]">
            <svg className="w-10 h-10 text-[var(--color-beige)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <h3 className="text-xl font-medium mb-3 tracking-wide">{uploading ? 'Analyzing...' : 'Drag & Drop files here'}</h3>
          <p className="text-[var(--color-slate)] text-sm mb-4">Support for PDF, JPG, PNG (Max 50MB)</p>
          
          {files.length > 0 && (
            <div className="w-full mt-4 flex flex-col items-center">
              <p className="text-xs text-[var(--color-slate)] uppercase tracking-[0.2em] mb-2">Processed Files</p>
              {files.map((f, i) => (
                <div key={i} className="text-sm text-[var(--color-beige)] bg-white/5 px-3 py-1 rounded-full mb-2">
                  {f}
                </div>
              ))}
            </div>
          )}

          {message && <p className="text-[var(--color-beige)] text-sm font-medium mt-4">{message}</p>}
        </div>

        <div className="ios-liquid-glass p-8 rounded-2xl flex-1 flex flex-col border border-white/5">
           <h3 className="text-xl font-medium mb-3 tracking-wide">Plain Language Analysis</h3>
           <p className="text-[var(--color-slate)] text-sm mb-6">Alternatively, describe your income, investments, and rent in plain English.</p>
           <textarea 
             value={textInput}
             onChange={e => setTextInput(e.target.value)}
             placeholder="e.g. I earn ₹12 lakhs, pay ₹20k monthly rent in Chennai, and invested ₹50k in PPF..."
             className="w-full flex-1 bg-white/5 border border-white/10 rounded-xl p-4 text-white placeholder-[var(--color-slate)]/50 focus:outline-none focus:border-[var(--color-beige)]/50 resize-none mb-4"
           ></textarea>
           <button onClick={handleTextSubmit} disabled={uploading} className="px-6 py-3 rounded-xl bg-[var(--color-beige)]/10 hover:bg-[var(--color-beige)]/20 text-[var(--color-beige)] font-medium transition-colors border border-[var(--color-beige)]/30 text-sm">
             Analyze Text
           </button>
        </div>
      </div>
    </div>
  );
}

function ReviewView() { 
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch('http://localhost:8001/api/dashboard')
      .then(res => res.json())
      .then(setData)
      .catch(console.error);
  }, []);

  const profile = data?.profile;

  return (
    <div className="animate-fade-in flex flex-col h-full flex-1">
      <h1 className="text-4xl md:text-5xl font-light mb-2 tracking-tight text-[var(--color-beige)]">Review</h1>
      <p className="text-[var(--color-slate)] text-lg mb-8">Review your CAI-extracted financial profile.</p>
      <div className="ios-liquid-glass p-8 rounded-2xl flex-1 overflow-y-auto">
        {profile ? (
          <div className="space-y-6">
             <div className="grid grid-cols-2 gap-6">
                <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                  <p className="text-xs text-[var(--color-slate)] uppercase tracking-wider mb-1">Annual Income</p>
                  <p className="text-xl">₹{profile.annual_income?.toLocaleString()}</p>
                </div>
                <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                  <p className="text-xs text-[var(--color-slate)] uppercase tracking-wider mb-1">Basic Salary</p>
                  <p className="text-xl">₹{profile.basic_salary?.toLocaleString()}</p>
                </div>
                <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                  <p className="text-xs text-[var(--color-slate)] uppercase tracking-wider mb-1">HRA Received</p>
                  <p className="text-xl">₹{profile.hra_received?.toLocaleString()}</p>
                </div>
                <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                  <p className="text-xs text-[var(--color-slate)] uppercase tracking-wider mb-1">Rent Paid</p>
                  <p className="text-xl">₹{profile.rent_paid?.toLocaleString()}</p>
                </div>
             </div>
             
             {profile.investments && Object.keys(profile.investments).length > 0 && (
               <div className="mt-8">
                 <h3 className="text-lg font-medium text-[var(--color-beige)] mb-4 border-b border-white/10 pb-2">Investments</h3>
                 <div className="grid grid-cols-2 gap-4">
                   {Object.entries(profile.investments).map(([key, val]: any) => (
                      <div key={key} className="flex justify-between p-3 bg-white/5 rounded-lg">
                        <span className="text-[var(--color-slate)]">{key}</span>
                        <span>₹{val.toLocaleString()}</span>
                      </div>
                   ))}
                 </div>
               </div>
             )}
          </div>
        ) : (
          <p className="text-[var(--color-slate)]">No data extracted yet. Please upload documents.</p>
        )}
      </div>
    </div>
  ); 
}

function DeductionsView() { 
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch('http://localhost:8001/api/dashboard')
      .then(res => res.json())
      .then(setData)
      .catch(console.error);
  }, []);

  const deductions = data?.deductions || [];

  return (
    <div className="animate-fade-in flex flex-col h-full flex-1">
      <h1 className="text-4xl md:text-5xl font-light mb-2 tracking-tight text-[var(--color-beige)]">Deductions</h1>
      <p className="text-[var(--color-slate)] text-lg mb-8">AI-discovered opportunities for tax savings.</p>
      <div className="ios-liquid-glass p-8 rounded-2xl flex-1 overflow-y-auto">
        {deductions.length > 0 ? (
          <div className="space-y-4">
            {deductions.map((d: any, i: number) => (
              <div key={i} className="bg-white/5 border border-white/10 rounded-xl p-6 hover:bg-white/10 transition-colors">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-lg font-medium text-white">Section {d.section}</h3>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${d.confidence === 'high' ? 'bg-green-500/20 text-green-300' : 'bg-yellow-500/20 text-yellow-300'}`}>
                    {d.confidence?.toUpperCase() || 'MEDIUM'}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-4 mt-4">
                  <div>
                    <p className="text-xs text-[var(--color-slate)] uppercase">Eligible</p>
                    <p className="font-mono text-[var(--color-beige)]">₹{d.eligible_amount?.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-xs text-[var(--color-slate)] uppercase">Claimed</p>
                    <p className="font-mono text-white">₹{d.claimed_amount?.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-xs text-[var(--color-slate)] uppercase">Status</p>
                    <p className="text-sm capitalize">{d.status}</p>
                  </div>
                </div>
                {d.reasoning && (
                  <p className="mt-4 text-sm text-[var(--color-slate)] border-t border-white/10 pt-3">{d.reasoning}</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[var(--color-slate)]">No deductions found yet. Upload data to begin analysis.</p>
        )}
      </div>
    </div>
  ); 
}

export default function App() {
  const [isResetting, setIsResetting] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8001/api/reset', { method: 'POST' })
      .catch(console.error)
      .finally(() => setIsResetting(false));
  }, []);

  if (isResetting) return <div className="bg-[#050505] min-h-screen text-white font-mono flex items-center justify-center">INITIALIZING CAI...</div>;

  return (
    <Router>
      <Layout />
    </Router>
  );
}
