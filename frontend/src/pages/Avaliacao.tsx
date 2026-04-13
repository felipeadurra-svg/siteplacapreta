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

  const steps = [
    { id: "form", label: "Dados do Veículo" },
    { id: "photos", label: "Enviar Fotos" },
    { id: "payment", label: "Pagamento Pix" },
    { id: "success", label: "Laudo Final" }
  ];

  const stepIndex: Record<Step, number> = { form: 0, photos: 1, payment: 2, success: 3 };

  // 1. CARREGA O SDK DO MERCADO PAGO
  useEffect(() => {
    if (document.getElementById("mp-sdk")) return;
    const script = document.createElement("script");
    script.id = "mp-sdk";
    script.src = "https://sdk.mercadopago.com/js/v2";
    script.async = true;
    document.body.appendChild(script);
  }, []);

  // 2. VIGIA O STATUS DO PAGAMENTO (SÓ MUDA DE TELA QUANDO O BACKEND DER OK)
  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (currentStep === "payment" && laudoId) {
      interval = setInterval(async () => {
        try {
          const response = await fetch(`https://siteplacapreta.onrender.com/check_status/${laudoId}`);
          if (response.ok) {
            const data = await response.json();
            // O Backend só retorna "ready" quando o pagamento for confirmado
            if (data.status === "ready") {
              setCurrentStep("success");
              clearInterval(interval);
            }
          }
        } catch (err) {
          console.log("Aguardando confirmação...");
        }
      }, 4000); // Verifica a cada 4 segundos
    }

    return () => clearInterval(interval);
  }, [currentStep, laudoId]);

  // 3. ENVIA FOTOS E GERA O LINK DE PAGAMENTO (SEM GERAR O RELATÓRIO AINDA)
  const handleUploadAndGoToPayment = async (currentPhotos: PhotoData) => {
    setIsProcessing(true);
    try {
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

      Object.entries(currentPhotos).forEach(([key, file]) => {
        if (file instanceof File) {
          submissionData.append(photoKeys[key] || `foto_${key}`, file);
        }
      });

      // Envia para o servidor salvar as fotos
      const resAvaliacao = await fetch("https://siteplacapreta.onrender.com/avaliacao", {
        method: "POST",
        body: submissionData
      });
      const dataAvaliacao = await resAvaliacao.json();

      if (dataAvaliacao.ok) {
        setLaudoId(dataAvaliacao.id);
        
        // Gera a Preferência do Mercado Pago
        const resPref = await fetch("https://siteplacapreta.onrender.com/create_preference", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ external_reference: dataAvaliacao.id })
        });
        const dataPref = await resPref.json();
        
        if (dataPref.id) {
          setPreferenceId(dataPref.id);
          setCurrentStep("payment"); // SÓ AGORA MUDA PARA A TELA DE PAGAMENTO
        }
      }
    } catch (err) {
      alert("Erro ao enviar dados. Tente novamente.");
    } finally {
      setIsProcessing(false);
    }
  };

  // 4. ABRE O CHECKOUT DO MERCADO PAGO AO CLICAR NO BOTÃO
  const handleOpenPayment = () => {
    if (!window.MercadoPago || !preferenceId) return;
    
    const mp = new window.MercadoPago('APP_USR-7bab0ee2-dbcf-43da-99b4-5f621e8e6074', {
      locale: 'pt-BR'
    });
    
    mp.checkout({
      preference: { id: preferenceId },
      autoOpen: true // Abre o modal ou janela do Mercado Pago
    });
  };

  return (
    <div className="min-h-screen bg-[#0f1115] text-slate-100">
      <Header />
      <main className="pt-28 pb-12 container px-4 max-w-5xl mx-auto">
        
        {/* PROGRESSO */}
        <nav className="mb-16 border border-white/10 bg-slate-800/30 rounded-2xl overflow-hidden">
          <ol className="flex divide-x divide-white/5">
            {steps.map((step, i) => (
              <li key={step.id} className="relative flex-1">
                <div className={`flex items-center gap-4 px-6 py-5 ${currentStep === step.id ? 'bg-black/20' : ''}`}>
                  <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border-2 ${
                    currentStep === step.id ? "bg-yellow-500 border-yellow-400 text-black shadow-[0_0_20px_rgba(234,179,8,0.3)]"
                    : stepIndex[currentStep] > i ? "bg-emerald-500/20 border-emerald-500/50 text-emerald-400"
                    : "bg-slate-900 border-slate-700 text-slate-500"
                  }`}>
                    {stepIndex[currentStep] > i ? <CheckCircle className="h-5 w-5" /> : (i + 1)}
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">PASSO 0{i+1}</span>
                    <span className={`text-sm font-black uppercase ${currentStep === step.id ? "text-white" : "text-slate-600"}`}>{step.label}</span>
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </nav>

        {/* CONTEÚDO */}
        <div className="bg-slate-900/50 border border-white/5 rounded-[2rem] p-8 shadow-2xl">
          
          {isProcessing && (
            <div className="flex flex-col items-center py-20 text-center">
              <Loader2 className="h-12 w-12 text-yellow-500 animate-spin mb-4" />
              <h3 className="text-2xl font-black uppercase">Enviando Dados...</h3>
              <p className="text-slate-500">Estamos preparando sua ficha técnica.</p>
            </div>
          )}

          {!isProcessing && currentStep === "form" && (
            <VehicleForm onSubmit={(data) => { setFormData(data); setCurrentStep("photos"); }} />
          )}

          {!isProcessing && currentStep === "photos" && (
            <PhotoUpload 
              onSubmit={(p) => handleUploadAndGoToPayment(p)} 
              onBack={() => setCurrentStep("form")}
            />
          )}

          {currentStep === "payment" && (
            <div className="max-w-md mx-auto py-8 text-center space-y-8">
              <div className="bg-[#161920] border border-white/10 p-8 rounded-[2rem] shadow-inner">
                <CreditCard className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
                <h2 className="text-2xl font-black uppercase mb-6">Pagar Avaliação</h2>
                
                <div className="flex justify-between items-center bg-black/40 p-5 rounded-2xl mb-8">
                  <span className="text-slate-400 font-bold uppercase text-xs">Valor Total</span>
                  <span className="text-3xl font-black text-white">R$ 1,00</span>
                </div>

                <Button 
                  className="w-full h-16 bg-yellow-500 hover:bg-yellow-400 text-black font-black text-lg rounded-2xl mb-6 shadow-lg shadow-yellow-500/20"
                  onClick={handleOpenPayment}
                >
                  PAGAR AGORA (PIX / CARTÃO)
                </Button>
                
                <div className="flex items-center justify-center gap-3">
                  <Loader2 className="h-4 w-4 text-yellow-500 animate-spin" />
                  <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Aguardando confirmação do banco...</span>
                </div>
              </div>
            </div>
          )}

          {currentStep === "success" && (
            <div className="py-12 text-center space-y-8">
              <div className="w-24 h-24 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto border border-emerald-500/20">
                <CheckCircle className="h-12 w-12 text-emerald-500" />
              </div>
              <h2 className="text-4xl font-black text-white uppercase italic tracking-tighter">Laudo Disponível!</h2>
              <Button 
                className="h-16 px-12 bg-white text-black font-black text-lg rounded-2xl hover:bg-slate-200 shadow-xl"
                onClick={() => window.open(`https://siteplacapreta.onrender.com/cliente/${laudoId}`, '_blank')}
              >
                VER MEU RELATÓRIO COMPLETO
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