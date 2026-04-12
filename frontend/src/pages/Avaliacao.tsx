import { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import VehicleForm, { type AvaliacaoFormData } from "@/components/VehicleForm";
import PhotoUpload, { type PhotoData } from "@/components/PhotoUpload";
import PaymentPage from "@/components/PaymentPage";
import { CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

type Step = "form" | "photos" | "payment" | "success";

// Declarar o objeto MercadoPago globalmente para o TypeScript não reclamar
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

  const steps = ["Dados", "Fotos", "Pagamento", "Concluído"];
  const stepIndex = { form: 0, photos: 1, payment: 2, success: 3 };

  // 📦 Carregar o Script do Mercado Pago
  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://sdk.mercadopago.com/js/v2";
    script.async = true;
    document.body.appendChild(script);
    return () => { document.body.removeChild(script); };
  }, []);

  const handleFormSubmit = (data: AvaliacaoFormData) => {
    setFormData(data);
    setCurrentStep("photos");
  };

  const handlePhotosSubmit = (photoData: PhotoData) => {
    setPhotos(photoData);
    setCurrentStep("payment");
  };

  // 🚀 ENVIO PARA BACKEND (Geração do Laudo via IA)
  const enviarParaBackend = async () => {
    if (!formData) return;
    const form = new FormData();
    form.append("nome", formData.nome);
    form.append("marca", formData.marca);
    form.append("modelo", formData.modelo);
    form.append("ano", formData.ano);

    Object.entries(photos).forEach(([key, file]) => {
      if (file instanceof File) {
        form.append(`foto_${key}`, file);
      }
    });

    const res = await fetch("https://siteplacapreta.onrender.com/avaliacao", {
      method: "POST",
      body: form,
    });

    if (!res.ok) throw new Error("Erro ao enviar avaliação");
    return await res.json();
  };

  // 💳 PROCESSO DE PAGAMENTO MERCADO PAGO
  const handlePayment = async () => {
    setIsProcessing(true);

    try {
      // 1. Criar preferência no backend
      const prefRes = await fetch("https://siteplacapreta.onrender.com/create_preference", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: [{ title: "Laudo Tecnico", unit_price: 99.90 }] })
      });
      
      const { id: preferenceId } = await prefRes.json();

      // 2. Abrir o modal do Mercado Pago
      const mp = new window.MercadoPago('APP_USR-9c54b89f-6fec-46ec-bde6-e975a8f1d962', {
        locale: 'pt-BR'
      });

      mp.checkout({
        preference: { id: preferenceId },
        autoOpen: true,
      });

      // Nota: Em um fluxo real, você esperaria o webhook. 
      // Aqui vamos simular que após o fechamento/pagamento ele gera o laudo.
      // Você pode ajustar para gerar o laudo APENAS após o sucesso nas back_urls.
      
      const respostaLaudo = await enviarParaBackend();
      if (respostaLaudo?.id) {
        setLaudoId(respostaLaudo.id);
      }

      setTimeout(() => {
        setIsProcessing(false);
        setCurrentStep("success");
      }, 2000);

    } catch (err) {
      console.error(err);
      setIsProcessing(false);
      alert("Erro ao processar pagamento ou gerar laudo.");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-16">
        <div className="container py-12 px-4">
          {/* STEPPER */}
          <div className="flex items-center justify-center gap-2 mb-12">
            {steps.map((label, i) => (
              <div key={label} className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                  stepIndex[currentStep] >= i ? "bg-yellow-500 text-black" : "bg-gray-300"
                }`}>
                  {i + 1}
                </div>
                <span className="text-xs">{label}</span>
              </div>
            ))}
          </div>

          {/* CONTEÚDO DINÂMICO */}
          {currentStep === "form" && <VehicleForm onSubmit={handleFormSubmit} />}
          {currentStep === "photos" && <PhotoUpload onSubmit={handlePhotosSubmit} onBack={() => setCurrentStep("form")} />}
          {currentStep === "payment" && <PaymentPage onPaymentConfirm={handlePayment} onBack={() => setCurrentStep("photos")} isProcessing={isProcessing} />}
          
          {currentStep === "success" && (
            <div className="text-center animate-in fade-in duration-700">
              <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
              <h2 className="text-2xl font-bold mt-4">Avaliação enviada com sucesso!</h2>
              <p className="text-gray-500 mt-2">O pagamento foi processado e seu laudo técnico já está disponível.</p>
              <div className="flex flex-col gap-3 items-center mt-6">
                <Button 
                  className="bg-green-700 hover:bg-green-800 text-white px-8 h-12 text-lg"
                  onClick={() => window.open(`https://siteplacapreta.onrender.com/cliente/${laudoId}`, '_blank')}
                >
                  Visualizar Laudo Técnico
                </Button>
                <Link to="/"><Button variant="ghost" className="mt-2">Voltar ao início</Button></Link>
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