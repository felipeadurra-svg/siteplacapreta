import { useState } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import VehicleForm, { type AvaliacaoFormData } from "@/components/VehicleForm";
import PhotoUpload, { type PhotoData } from "@/components/PhotoUpload";
import PaymentPage from "@/components/PaymentPage";
import { CheckCircle, FileText, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

type Step = "form" | "photos" | "payment" | "success";

const Avaliacao = () => {
  const [currentStep, setCurrentStep] = useState<Step>("form");
  const [formData, setFormData] = useState<AvaliacaoFormData | null>(null);
  const [photos, setPhotos] = useState<PhotoData>({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [laudoHtml, setLaudoHtml] = useState<string | null>(null); // Armazena o laudo gerado

  const stepIndex = { form: 0, photos: 1, payment: 2, success: 3 };
  const steps = ["Dados", "Fotos", "Pagamento", "Resultado"];

  const handleFormSubmit = (data: AvaliacaoFormData) => {
    setFormData(data);
    setCurrentStep("photos");
  };

  const handlePhotosSubmit = (photoData: PhotoData) => {
    setPhotos(photoData);
    setCurrentStep("payment");
  };

  const enviarParaBackend = async () => {
    if (!formData) return;
    const form = new FormData();

    // Cliente e Veículo
    form.append("nome", formData.nome);
    form.append("marca", formData.marca);
    form.append("modelo", formData.modelo);
    form.append("ano", formData.ano);

    // Fotos
    Object.entries(photos).forEach(([key, file]) => {
      if (file instanceof File) {
        form.append(`foto_${key}`, file);
      }
    });

    const res = await fetch("https://siteplacapreta.onrender.com/avaliacao", {
      method: "POST",
      body: form,
    });

    if (!res.ok) throw new Error("Erro ao gerar laudo");
    return await res.json();
  };

  const handlePayment = async () => {
    setIsProcessing(true);
    try {
      const resposta = await enviarParaBackend();
      
      if (resposta.html_laudo) {
        setLaudoHtml(resposta.html_laudo); // Salva o HTML recebido
        setCurrentStep("success");
      }
    } catch (err) {
      console.error(err);
      alert("Erro ao processar avaliação. Tente novamente.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="pt-16">
        <div className="container py-12 px-4">

          {/* Stepper Visual */}
          <div className="flex items-center justify-center gap-2 mb-12">
            {steps.map((label, i) => (
              <div key={label} className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                  stepIndex[currentStep] >= i ? "bg-yellow-500 text-black" : "bg-gray-300"
                }`}>
                  {i + 1}
                </div>
                <span className="hidden sm:inline text-xs">{label}</span>
              </div>
            ))}
          </div>

          {/* Lógica de Etapas */}
          {currentStep === "form" && <VehicleForm onSubmit={handleFormSubmit} />}

          {currentStep === "photos" && (
            <PhotoUpload onSubmit={handlePhotosSubmit} onBack={() => setCurrentStep("form")} />
          )}

          {currentStep === "payment" && (
            <PaymentPage 
              onPaymentConfirm={handlePayment} 
              onBack={() => setCurrentStep("photos")} 
              isProcessing={isProcessing} 
            />
          )}

          {currentStep === "success" && (
            <div className="max-w-4xl mx-auto">
              <div className="bg-green-50 border border-green-200 p-6 rounded-lg mb-8 text-center">
                <CheckCircle className="mx-auto h-12 w-12 text-green-500 mb-2" />
                <h2 className="text-2xl font-bold text-green-800">Pagamento Confirmado e Laudo Gerado!</h2>
                <p className="text-green-700">Veja abaixo o resultado da sua perícia técnica.</p>
                <div className="mt-4 flex justify-center gap-4">
                    <Button onClick={() => window.print()} variant="outline" className="gap-2">
                        <Download size={18} /> Baixar PDF
                    </Button>
                    <Link to="/">
                        <Button className="gap-2"> <FileText size={18} /> Nova Avaliação</Button>
                    </Link>
                </div>
              </div>

              {/* RENDERIZAÇÃO DO LAUDO VINDO DO BACKEND */}
              {laudoHtml ? (
                <div 
                  className="laudo-container shadow-2xl rounded-lg overflow-hidden bg-white"
                  dangerouslySetInnerHTML={{ __html: laudoHtml }} 
                />
              ) : (
                <div className="p-20 text-center">Carregando laudo...</div>
              )}
            </div>
          )}

        </div>
      </main>

      <Footer />
    </div>
  );
};

export default Avaliacao;