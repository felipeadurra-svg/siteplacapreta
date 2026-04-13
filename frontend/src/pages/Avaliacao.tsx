import { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import VehicleForm, { type AvaliacaoFormData } from "@/components/VehicleForm";
import PhotoUpload, { type PhotoData } from "@/components/PhotoUpload";
import { CheckCircle, CreditCard, ArrowLeft, Loader2, ExternalLink, ShieldCheck, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

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
  const [isRetrying, setIsRetrying] = useState(false);

  // --- CONSTANTES DE NAVEGAÇÃO ---
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

  // Função para buscar a preferência de pagamento
  const fetchPreference = async () => {
    if (preferenceId) return;
    
    setIsRetrying(true);
    setErrorLoadingPayment(false);
    
    try {
      const prefRes = await fetch("https://siteplacapreta.onrender.com/create_preference", {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      
      if (!prefRes.ok) throw new Error("Backend não respondeu corretamente");
      
      const data = await prefRes.json();
      if (data.id) {
        setPreferenceId(data.id);
      } else {
        throw new Error("ID de preferência ausente");
      }
    } catch (err) {
      console.error("Erro na conexão:", err);
      setErrorLoadingPayment(true);
    } finally {
      setIsRetrying(false);
    }
  };

  // Tenta buscar a preferência ao entrar na tela de pagamento
  useEffect(() => {
    if (currentStep === "payment") {
      fetchPreference();
    }
  }, [currentStep]);

  const handleFormSubmit = (data: AvaliacaoFormData) => {
    setFormData(data);
    setCurrentStep("photos");
  };

  const handlePhotosSubmit = (photoData: PhotoData) => {
    setPhotos(photoData);
    setCurrentStep("payment");
  };

  const handlePaymentAndGenerate = async () => {
    if (!window.MercadoPago || !preferenceId) return;

    setIsProcessing(true);

    try {
      const mp = new window.MercadoPago('APP_USR-9c54b89f-6fec-46ec-bde6-e975a8f1d962', {
        locale: 'pt-BR'
      });

      mp.checkout({
        preference: { id: preferenceId },
        autoOpen: true,
      });

      const form = new FormData();
      if (formData) {
        form.append("nome", formData.nome);
        form.append("marca", formData.marca);
        form.append("modelo", formData.modelo);
        form.append("ano", formData.ano);
      }

      Object.entries(photos).forEach(([key, file]) => {
        if (file instanceof File) form.append(`foto_${key}`, file);
      });

      const res = await fetch("https://siteplacapreta.onrender.com/avaliacao", {
        method: "POST",
        body: form,
      });

      const respostaLaudo = await res.json();
      
      if (respostaLaudo?.id) {
        setLaudoId(respostaLaudo.id);
        setTimeout(() => {
            setCurrentStep("success");
            setIsProcessing(false);
        }, 3000);
      }
    } catch (err) {
      console.error(err);
      setIsProcessing(false);
      alert("Erro ao processar. Verifique bloqueadores de pop-up.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <main className="pt-16">
        <div className="container py-12 px-4 max-w-4xl mx-auto">
          
          {/* STEPPER - CORRIGIDO: Agora 'steps' está definido */}
          <div className="flex items-center justify-center gap-4 mb-12">
            {steps.map((label, i) => (
              <div key={label} className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                  stepIndex[currentStep] >= i ? "bg-yellow-500 text-black shadow-lg" : "bg-white border border-slate-200 text-slate-400"
                }`}>
                  {i + 1}
                </div>
                <span className={`text-xs hidden md:inline ${stepIndex[currentStep] === i ? "font-bold text-slate-900" : "text-slate-400"}`}>
                  {label}
                </span>
              </div>
            ))}
          </div>

          {currentStep === "form" && <VehicleForm onSubmit={handleFormSubmit} />}
          {currentStep === "photos" && <PhotoUpload onSubmit={handlePhotosSubmit} onBack={() => setCurrentStep("form")} />}
          
          {currentStep === "payment" && (
            <div className="max-w-md mx-auto p-8 bg-white rounded-3xl shadow-2xl border border-slate-100">
              <div className="text-center space-y-6">
                <div className="bg-yellow-50 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-2">
                  <CreditCard className="h-10 w-10 text-yellow-600" />
                </div>
                
                <div className="space-y-2">
                  <h2 className="text-3xl font-black text-slate-900 tracking-tight underline decoration-yellow-500">PAGAMENTO</h2>
                  <p className="text-slate-500 text-sm">Gere seu laudo técnico certificado.</p>
                </div>
                
                <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100 text-left space-y-3">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-500 font-medium">Serviço:</span>
                    <span className="font-bold text-slate-900">Relatório Pericial IA</span>
                  </div>
                  <div className="flex justify-between items-center border-t border-slate-200 pt-3">
                    <span className="text-slate-900 font-bold">Total:</span>
                    <span className="text-2xl font-black text-emerald-600">R$ 100,00</span>
                  </div>
                </div>

                {errorLoadingPayment && (
                  <div className="p-4 bg-red-50 border border-red-100 rounded-xl space-y-3">
                    <div className="flex items-center gap-2 text-red-600 text-sm font-bold justify-center">
                      <AlertCircle className="h-4 w-4" />
                      Falha na conexão com o servidor
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full text-red-600 border-red-200 hover:bg-red-100 font-bold"
                      onClick={fetchPreference}
                    >
                      <RefreshCw className={`h-3 w-3 mr-2 ${isRetrying ? 'animate-spin' : ''}`} />
                      Tentar Conectar Agora
                    </Button>
                  </div>
                )}

                <div className="flex flex-col gap-4">
                  <Button 
                    className="w-full h-16 text-lg bg-yellow-500 hover:bg-yellow-600 text-black font-black rounded-2xl shadow-xl transition-all active:scale-95 disabled:opacity-40"
                    onClick={handlePaymentAndGenerate}
                    disabled={isProcessing || !preferenceId || isRetrying}
                  >
                    {isProcessing ? (
                      <div className="flex items-center gap-3">
                        <Loader2 className="animate-spin h-6 w-6" />
                        <span>AGUARDE...</span>
                      </div>
                    ) : isRetrying || (!preferenceId && !errorLoadingPayment) ? (
                      <div className="flex items-center gap-3">
                        <Loader2 className="animate-spin h-5 w-5" />
                        <span>CONECTANDO...</span>
                      </div>
                    ) : (
                      "PAGAR AGORA"
                    )}
                  </Button>
                  
                  <Button variant="ghost" onClick={() => setCurrentStep("photos")} disabled={isProcessing} className="text-slate-400 font-bold">
                    <ArrowLeft className="w-4 h-4 mr-2" /> Voltar
                  </Button>
                </div>

                <div className="flex items-center justify-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-t pt-4">
                   <ShieldCheck className="w-4 h-4 text-emerald-500" />
                   Checkout Seguro & Criptografado
                </div>
              </div>
            </div>
          )}
          
          {currentStep === "success" && (
            <div className="text-center max-w-md mx-auto animate-in zoom-in-95 duration-500">
              <div className="bg-emerald-500 w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-8 shadow-2xl border-4 border-white">
                <CheckCircle className="h-12 w-12 text-white" />
              </div>
              <h2 className="text-4xl font-black mb-4 text-slate-900 tracking-tight uppercase">SUCESSO!</h2>
              <p className="text-slate-600 mb-10 leading-relaxed text-lg">
                O pagamento foi processado e seu laudo está pronto para visualização.
              </p>
              
              <div className="space-y-4">
                <Button 
                  className="w-full bg-slate-900 hover:bg-black text-white h-20 text-xl font-black shadow-2xl flex items-center justify-center gap-4 transition-transform hover:scale-105"
                  onClick={() => window.open(`https://siteplacapreta.onrender.com/cliente/${laudoId}`, '_blank')}
                >
                  <ExternalLink className="w-6 h-6 text-yellow-500" />
                  VER LAUDO TÉCNICO
                </Button>
                
                <Link to="/" className="block">
                  <Button variant="ghost" className="w-full h-12 text-slate-400 font-bold uppercase tracking-tighter">
                    VOLTAR AO INÍCIO
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Avaliacao;