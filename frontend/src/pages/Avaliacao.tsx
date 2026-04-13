import { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import VehicleForm, { type AvaliacaoFormData } from "@/components/VehicleForm";
import PhotoUpload, { type PhotoData } from "@/components/PhotoUpload";
import { CheckCircle, CreditCard, Loader2, ShieldCheck, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

// Definição dos passos do formulário
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

  // Carrega o SDK do Mercado Pago
  useEffect(() => {
    if (document.getElementById("mp-sdk")) return;
    const script = document.createElement("script");
    script.id = "mp-sdk";
    script.src = "https://sdk.mercadopago.com/js/v2";
    script.async = true;
    document.body.appendChild(script);
  }, []);

  // Gera a preferência de pagamento assim que chegar na tela de pagamento
  const fetchPreference = async () => {
    setErrorLoadingPayment(false);
    try {
      // Endpoint corrigido para bater com o seu backend no Render
      const res = await fetch("https://siteplacapreta.onrender.com/create_preference", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}) // Enviando corpo vazio para evitar erro 422
      });
      
      const data = await res.json();
      if (data.id) {
        setPreferenceId(data.id);
      } else {
        throw new Error("ID de preferência não retornado");
      }
    } catch (err) {
      console.error("Erro ao gerar pagamento:", err);
      setErrorLoadingPayment(true);
    }
  };

  useEffect(() => {
    if (currentStep === "payment") {
      fetchPreference();
    }
  }, [currentStep]);

  // Função principal que processa o pagamento e envia os dados para o backend
  const handlePaymentAndGenerate = async () => {
    if (!window.MercadoPago || !preferenceId) return;

    setIsProcessing(true);
    
    try {
      // 1. Abre o Checkout Pro do Mercado Pago
      const mp = new window.MercadoPago('APP_USR-9c54b89f-6fec-46ec-bde6-e975a8f1d962', {
        locale: 'pt-BR'
      });
      
      mp.checkout({
        preference: { id: preferenceId },
        autoOpen: true
      });

      // 2. Prepara os dados para o backend (Multipart FormData)
      const submissionData = new FormData();
      
      if (formData) {
        submissionData.append("nome", formData.nome);
        submissionData.append("marca", formData.marca);
        submissionData.append("modelo", formData.modelo);
        submissionData.append("ano", formData.ano);
      }

      // Mapeamento exato das chaves que o backend espera
      const photoKeys: Record<string, string> = {
        frente: "foto_frente",
        traseira: "foto_traseira",
        lateralDireita: "foto_lateral_direita",
        lateralEsquerda: "foto_lateral_esquerda",
        interior: "foto_interior",
        painel: "foto_painel",
        motor: "foto_motor",
        chassi: "foto_chassi"
      };

      Object.entries(photos).forEach(([key, file]) => {
        if (file instanceof File) {
          const backendKey = photoKeys[key] || `foto_${key}`;
          submissionData.append(backendKey, file);
        }
      });

      // 3. Envia para o backend processar a IA
      const res = await fetch("https://siteplacapreta.onrender.com/avaliacao", {
        method: "POST",
        body: submissionData
      });

      const data = await res.json();

      if (data.ok) {
        setLaudoId(data.id);
        // Pequeno delay para o usuário ver o feedback de "processando"
        setTimeout(() => setCurrentStep("success"), 2000);
      } else {
        throw new Error("Erro no processamento do laudo");
      }

    } catch (err) {
      console.error(err);
      alert("Houve um erro ao processar sua solicitação. Por favor, tente novamente.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      
      <main className="pt-24 pb-12 container px-4 max-w-4xl mx-auto">
        {/* Barra de Progresso */}
        <div className="flex items-center justify-between mb-12 relative">
          <div className="absolute top-1/2 left-0 w-full h-0.5 bg-slate-200 -z-10"></div>
          {steps.map((label, i) => (
            <div key={label} className="flex flex-col items-center gap-2 bg-slate-50 px-2">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-all ${
                stepIndex[currentStep] >= i 
                ? "bg-yellow-500 border-yellow-500 text-black shadow-lg shadow-yellow-200" 
                : "bg-white border-slate-200 text-slate-400"
              }`}>
                {i + 1}
              </div>
              <span className={`text-xs font-bold uppercase tracking-tighter ${
                stepIndex[currentStep] >= i ? "text-slate-900" : "text-slate-400"
              }`}>
                {label}
              </span>
            </div>
          ))}
        </div>

        {/* Passo 1: Formulário de Dados */}
        {currentStep === "form" && (
          <VehicleForm 
            onSubmit={(data) => {
              setFormData(data);
              setCurrentStep("photos");
            }} 
          />
        )}

        {/* Passo 2: Upload de Fotos */}
        {currentStep === "photos" && (
          <PhotoUpload 
            onSubmit={(p) => {
              setPhotos(p);
              setCurrentStep("payment");
            }} 
            onBack={() => setCurrentStep("form")}
          />
        )}
        
        {/* Passo 3: Pagamento */}
        {currentStep === "payment" && (
          <div className="max-w-md mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="bg-white rounded-3xl shadow-2xl overflow-hidden border border-slate-100">
              <div className="bg-slate-900 p-8 text-center text-white">
                <CreditCard className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
                <h2 className="text-2xl font-black italic">PAGAMENTO</h2>
                <p className="text-slate-400 text-sm">Checkout Seguro via Mercado Pago</p>
              </div>

              <div className="p-8 space-y-6">
                <div className="space-y-4">
                  <div className="flex justify-between items-center pb-4 border-bottom border-dashed border-slate-200">
                    <span className="text-slate-600 font-medium">Laudo Técnico Pericial</span>
                    <span className="text-xl font-black text-slate-900">R$ 99,90</span>
                  </div>
                  <div className="flex gap-2 text-emerald-600 bg-emerald-50 p-3 rounded-xl text-xs font-bold">
                    <ShieldCheck className="h-4 w-4" />
                    SEU LAUDO SERÁ GERADO IMEDIATAMENTE APÓS O PAGAMENTO
                  </div>
                </div>

                {errorLoadingPayment ? (
                  <div className="text-center p-4 bg-red-50 rounded-xl">
                    <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
                    <p className="text-sm text-red-600 font-bold mb-3">Erro ao carregar o pagamento.</p>
                    <Button onClick={fetchPreference} variant="outline" className="text-xs uppercase">
                      Tentar Novamente
                    </Button>
                  </div>
                ) : (
                  <Button 
                    className="w-full h-16 bg-yellow-500 hover:bg-yellow-600 text-black font-black text-lg shadow-xl shadow-yellow-100 transition-all active:scale-95" 
                    onClick={handlePaymentAndGenerate} 
                    disabled={!preferenceId || isProcessing}
                  >
                    {isProcessing ? (
                      <div className="flex items-center gap-3">
                        <Loader2 className="animate-spin h-5 w-5" />
                        PROCESSANDO...
                      </div>
                    ) : (
                      "PAGAR E GERAR LAUDO"
                    )}
                  </Button>
                )}
                
                <p className="text-[10px] text-center text-slate-400 uppercase font-bold tracking-widest">
                  Ambiente Criptografado de Ponta a Ponta
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Passo 4: Sucesso */}
        {currentStep === "success" && (
          <div className="max-w-md mx-auto text-center space-y-8 animate-in zoom-in-95 duration-700">
            <div className="relative inline-block">
              <div className="absolute inset-0 bg-emerald-200 blur-3xl rounded-full opacity-50 animate-pulse"></div>
              <CheckCircle className="h-24 w-24 text-emerald-500 relative z-10 mx-auto" />
            </div>
            
            <div className="space-y-2">
              <h2 className="text-3xl font-black text-slate-900 italic">LAUDO GERADO!</h2>
              <p className="text-slate-600 font-medium">
                Seu veículo foi analisado com sucesso pela nossa perícia técnica.
              </p>
            </div>

            <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xl space-y-4">
              <Button 
                className="w-full h-16 bg-slate-900 hover:bg-slate-800 text-white font-black text-lg transition-all"
                onClick={() => window.open(`https://siteplacapreta.onrender.com/cliente/${laudoId}`, '_blank')}
              >
                VISUALIZAR LAUDO COMPLETO
              </Button>
              <p className="text-xs text-slate-400 font-bold uppercase">
                ID do Laudo: {laudoId}
              </p>
            </div>
            
            <Button variant="ghost" className="text-slate-400 font-bold" onClick={() => window.location.reload()}>
              REALIZAR NOVA AVALIAÇÃO
            </Button>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
};

export default Avaliacao;