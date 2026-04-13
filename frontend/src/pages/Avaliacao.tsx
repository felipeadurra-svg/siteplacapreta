import { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import VehicleForm, { type AvaliacaoFormData } from "@/components/VehicleForm";
import PhotoUpload, { type PhotoData } from "@/components/PhotoUpload";
import { CheckCircle, CreditCard, Loader2, ShieldCheck, AlertCircle } from "lucide-react";
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

  const steps = ["Dados", "Fotos", "Pagamento", "Concluído"];
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
    <div className="min-h-screen bg-slate-950 text-white"> {/* Fundo Escuro */}
      <Header />
      
      <main className="pt-24 pb-12 container px-4 max-w-4xl mx-auto">
        {/* Barra de Progresso Invertida */}
        <div className="flex items-center justify-between mb-12 relative">
          <div className="absolute top-1/2 left-0 w-full h-0.5 bg-slate-800 -z-10"></div>
          {steps.map((label, i) => (
            <div key={label} className="flex flex-col items-center gap-2 bg-slate-950 px-2">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-all ${
                stepIndex[currentStep] >= i 
                ? "bg-yellow-500 border-yellow-500 text-black shadow-lg shadow-yellow-500/20" 
                : "bg-slate-900 border-slate-800 text-slate-500"
              }`}>
                {i + 1}
              </div>
              <span className={`text-[10px] font-bold uppercase tracking-widest ${
                stepIndex[currentStep] >= i ? "text-yellow-500" : "text-slate-600"
              }`}>
                {label}
              </span>
            </div>
          ))}
        </div>

        {/* Containers do Form e Fotos com Fundo Escuro */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl">
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
        </div>
        
        {/* Seção de Pagamento */}
        {currentStep === "payment" && (
          <div className="max-w-md mx-auto mt-8 animate-in fade-in slide-in-from-bottom-4">
            <div className="bg-slate-900 rounded-3xl shadow-2xl overflow-hidden border border-slate-800">
              <div className="bg-black p-8 text-center text-white">
                <CreditCard className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
                <h2 className="text-2xl font-black italic uppercase">PAGAMENTO</h2>
                <p className="text-slate-500 text-sm">Checkout Seguro via Mercado Pago</p>
              </div>

              <div className="p-8 space-y-6">
                <div className="space-y-4">
                  <div className="flex justify-between items-center pb-4 border-b border-dashed border-slate-800">
                    <span className="text-slate-400 font-medium">Laudo Técnico Pericial</span>
                    <span className="text-xl font-black text-white">R$ 99,90</span>
                  </div>
                </div>

                <Button 
                  className="w-full h-16 bg-yellow-500 hover:bg-yellow-600 text-black font-black text-lg shadow-xl shadow-yellow-500/10 transition-all active:scale-95" 
                  onClick={handlePaymentAndGenerate} 
                  disabled={!preferenceId || isProcessing}
                >
                  {isProcessing ? "PROCESSANDO..." : "PAGAR E GERAR LAUDO"}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Sucesso */}
        {currentStep === "success" && (
          <div className="max-w-md mx-auto text-center space-y-8 mt-12">
            <CheckCircle className="h-24 w-24 text-emerald-500 mx-auto" />
            <h2 className="text-3xl font-black text-white italic uppercase">LAUDO GERADO!</h2>
            <Button 
              className="w-full h-16 bg-white text-black font-black text-lg hover:bg-slate-200"
              onClick={() => window.open(`https://siteplacapreta.onrender.com/cliente/${laudoId}`, '_blank')}
            >
              VISUALIZAR LAUDO
            </Button>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
};

export default Avaliacao;