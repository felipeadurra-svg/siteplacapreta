import { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import VehicleForm, { type AvaliacaoFormData } from "@/components/VehicleForm";
import PhotoUpload, { type PhotoData } from "@/components/PhotoUpload";
import { CheckCircle, CreditCard, Loader2, ShieldCheck, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

type Step = "form" | "photos" | "payment" | "success";

declare global {
  interface Window {
    MercadoPago: any;
  }
}

const Avaliacao = () => {
  const [currentStep, setCurrentStep] = useState<Step>("form");
  const [formData, setFormData] = useState<AvaliacaoFormData | null>(null);
  const [photos, setPhotos] = useState<PhotoData>({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [laudoId, setLaudoId] = useState<string | null>(null);
  const [preferenceId, setPreferenceId] = useState<string | null>(null);
  const [errorLoadingPayment, setErrorLoadingPayment] = useState(false);

  // Mudei o nome para facilitar o mapeamento visual
  const steps = [
    { id: "form", label: "Dados do Veículo" },
    { id: "photos", label: "Enviar Fotos" },
    { id: "payment", label: "Pagamento Pix" },
    { id: "success", label: "Laudo Final" }
  ];
  const stepIndex: Record<Step, number> = { form: 0, photos: 1, payment: 2, success: 3 };

  useEffect(() => {
    if (document.getElementById("mp-sdk")) return;
    const script = document.createElement("script");
    script.id = "mp-sdk";
    script.src = "https://sdk.mercadopago.com/js/v2";
    script.async = true;
    document.body.appendChild(script);
  }, []);

  const fetchPreference = async () => {
    setErrorLoadingPayment(false);
    try {
      const res = await fetch("https://siteplacapreta.onrender.com/create_preference", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}) 
      });
      const data = await res.json();
      if (data.id) setPreferenceId(data.id);
    } catch (err) {
      setErrorLoadingPayment(true);
    }
  };

  useEffect(() => {
    if (currentStep === "payment") fetchPreference();
  }, [currentStep]);

  const handlePaymentAndGenerate = async () => {
    if (!window.MercadoPago || !preferenceId) return;
    setIsProcessing(true);
    try {
      const mp = new window.MercadoPago('APP_USR-7bab0ee2-dbcf-43da-99b4-5f621e8e6074', {
        locale: 'pt-BR'
      });
      mp.checkout({ preference: { id: preferenceId }, autoOpen: true });

      const submissionData = new FormData();
      if (formData) {
        submissionData.append("nome", formData.nome);
        submissionData.append("marca", formData.marca);
        submissionData.append("modelo", formData.modelo);
        submissionData.append("ano", formData.ano);
      }

      const photoKeys: Record<string, string> = {
        frente: "foto_frente", traseira: "foto_traseira", lateralDireita: "foto_lateral_direita",
        lateralEsquerda: "foto_lateral_esquerda", interior: "foto_interior", painel: "foto_painel",
        motor: "foto_motor", chassi: "foto_chassi"
      };

      Object.entries(photos).forEach(([key, file]) => {
        if (file instanceof File) {
          const backendKey = photoKeys[key] || `foto_${key}`;
          submissionData.append(backendKey, file);
        }
      });

      const res = await fetch("https://siteplacapreta.onrender.com/avaliacao", {
        method: "POST",
        body: submissionData
      });
      const data = await res.json();
      if (data.ok) {
        setLaudoId(data.id);
        setTimeout(() => setCurrentStep("success"), 2000);
      }
    } catch (err) {
      alert("Erro ao processar. Tente novamente.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0f1115] text-slate-100 selection:bg-yellow-500/30">
      <Header />
      
      <main className="pt-28 pb-12 container px-4 max-w-5xl mx-auto">
        
        {/* NOVA BARRA DE PROGRESSO COM SETAS (CHEVRONS) */}
        <nav className="mb-16 border border-white/5 bg-[#14161b] rounded-2xl overflow-hidden shadow-2xl">
          <ol className="flex divide-x divide-white/5">
            {steps.map((step, i) => {
              const isActive = currentStep === step.id;
              const isCompleted = stepIndex[currentStep] > i;
              
              return (
                <li key={step.id} className="relative flex-1 group">
                  <div className={`flex items-center gap-4 px-6 py-5 text-sm transition-colors duration-300 ${isActive || isCompleted ? 'bg-black/40' : ''}`}>
                    
                    {/* Número/Ícone do Passo */}
                    <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border-2 transition-all duration-300 ${
                      isActive 
                        ? "bg-yellow-500 border-yellow-400 text-black shadow-[0_0_15px_rgba(234,179,8,0.2)]"
                        : isCompleted
                          ? "bg-emerald-500/10 border-emerald-500 text-emerald-500"
                          : "bg-slate-900 border-slate-800 text-slate-600"
                    }`}>
                      {isCompleted ? <CheckCircle className="h-5 w-5" /> : (i + 1)}
                    </div>
                    
                    {/* Texto do Passo */}
                    <div className="flex flex-col">
                      <span className={`text-[10px] font-bold uppercase tracking-widest ${isActive ? "text-slate-400" : "text-slate-600"}`}>PASSO 0{i+1}</span>
                      <span className={`text-sm font-black tracking-tight ${
                        isActive 
                        ? "text-white" 
                        : isCompleted
                          ? "text-slate-300"
                          : "text-slate-500"
                      }`}>{step.label}</span>
                    </div>

                    {/* A Flexinha Indicadora (apenas entre os passos) */}
                    {i < steps.length - 1 && (
                      <div className="absolute top-1/2 -right-3 -translate-y-1/2 z-10 p-1 bg-[#14161b] rounded-full border border-white/5 group-hover:border-yellow-500/30 transition-colors">
                        <ChevronRight className={`h-4 w-4 ${isCompleted || isActive ? 'text-yellow-500/50' : 'text-slate-700'}`} />
                      </div>
                    )}
                  </div>
                </li>
              );
            })}
          </ol>
        </nav>

        {/* Card Principal - Glassmorphism */}
        <div className="bg-slate-900/50 backdrop-blur-md border border-white/5 rounded-[2rem] p-8 shadow-2xl">
          {currentStep === "form" && (
            <VehicleForm 
              onSubmit={(data) => {
                setFormData(data);
                setCurrentStep("photos");
              }} 
            />
          )}

          {currentStep === "photos" && (
            <PhotoUpload 
              onSubmit={(p) => {
                setPhotos(p);
                setCurrentStep("payment");
              }} 
              onBack={() => setCurrentStep("form")}
            />
          )}

          {currentStep === "payment" && (
            <div className="max-w-md mx-auto py-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="bg-[#161920] rounded-[2rem] border border-white/10 overflow-hidden shadow-inner">
                <div className="p-8 text-center border-b border-white/5 bg-gradient-to-b from-white/5 to-transparent">
                  <div className="inline-flex p-4 rounded-2xl bg-yellow-500/10 mb-4">
                    <CreditCard className="h-10 w-10 text-yellow-500" />
                  </div>
                  <h2 className="text-2xl font-black tracking-tighter italic uppercase text-white">Pagamento Seguro</h2>
                  <p className="text-slate-500 text-xs mt-1">Sua avaliação técnica está a um passo</p>
                </div>

                <div className="p-8 space-y-8">
                  <div className="flex justify-between items-end">
                    <span className="text-slate-500 text-sm font-bold uppercase tracking-widest">Valor Total</span>
                    <span className="text-4xl font-black text-white leading-none">R$ 99,90</span>
                  </div>

                  <div className="space-y-4">
                    <Button 
                      className="w-full h-16 bg-yellow-500 hover:bg-yellow-400 text-black font-black text-lg rounded-2xl shadow-[0_10px_30px_rgba(234,179,8,0.15)] transition-all hover:-translate-y-1 active:scale-95 disabled:opacity-50" 
                      onClick={handlePaymentAndGenerate} 
                      disabled={!preferenceId || isProcessing}
                    >
                      {isProcessing ? (
                        <span className="flex items-center gap-2"><Loader2 className="animate-spin" /> PROCESSANDO...</span>
                      ) : "GERAR QR CODE PIX"}
                    </Button>
                    
                    <div className="flex items-center justify-center gap-2 text-[10px] text-slate-500 font-bold uppercase tracking-tighter">
                      <ShieldCheck className="h-3 w-3 text-emerald-500" />
                      Pagamento processado pelo Mercado Pago
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {currentStep === "success" && (
            <div className="py-12 text-center space-y-8 animate-in zoom-in-95 duration-700">
              <div className="w-24 h-24 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto border border-emerald-500/20 shadow-[0_0_50px_rgba(16,185,129,0.1)]">
                <CheckCircle className="h-12 w-12 text-emerald-500" />
              </div>
              <div>
                <h2 className="text-4xl font-black text-white italic tracking-tighter uppercase mb-2">Laudo Pronto!</h2>
                <p className="text-slate-400">A inteligência artificial concluiu a análise do seu clássico.</p>
              </div>
              <Button 
                className="h-16 px-12 bg-white text-black font-black text-lg rounded-2xl hover:bg-slate-200 transition-colors shadow-lg shadow-black/20"
                onClick={() => window.open(`https://siteplacapreta.onrender.com/cliente/${laudoId}`, '_blank')}
              >
                ACESSAR RELATÓRIO TÉCNICO
              </Button>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Avaliacao;