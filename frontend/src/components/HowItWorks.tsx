import { ClipboardList, Camera, CreditCard, FileText } from "lucide-react";
import carInterior from "@/assets/car-interior.jpg";

const steps = [
  {
    icon: ClipboardList,
    title: "Preencha seus dados",
    description: "Informe os dados do proprietário e do veículo para iniciarmos a avaliação.",
  },
  {
    icon: Camera,
    title: "Envie as fotos",
    description: "Envie fotos detalhadas do veículo: exterior, interior, motor, chassi e mais.",
  },
  {
    icon: CreditCard,
    title: "Realize o pagamento",
    description: "Pagamento seguro com valor fixo. Após a confirmação, a análise será iniciada.",
  },
  {
    icon: FileText,
    title: "Receba o relatório",
    description: "Relatório técnico completo com pontuação, análise detalhada e certificação.",
  },
];

const HowItWorks = () => {
  return (
    <section id="como-funciona" className="relative py-24 overflow-hidden">
      {/* Background image */}
      <div className="absolute inset-0">
        <img
          src={carInterior}
          alt=""
          loading="lazy"
          width={1280}
          height={720}
          className="w-full h-full object-cover opacity-10"
        />
        <div className="absolute inset-0 bg-card/90" />
      </div>

      <div className="container relative z-10 px-4">
        <div className="text-center mb-16">
          <span className="text-xs uppercase tracking-[0.3em] text-primary font-medium">
            Processo Simples
          </span>
          <h2 className="font-heading text-3xl md:text-4xl font-bold mt-3">
            Como <span className="text-gradient-gold">Funciona</span>
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-5xl mx-auto">
          {steps.map((step, index) => (
            <div
              key={index}
              className="relative group flex flex-col items-center text-center p-6 rounded-xl border border-border bg-background/60 backdrop-blur-sm hover:bg-background/80 transition-all duration-300 hover:glow-gold"
            >
              <div className="flex items-center justify-center w-14 h-14 rounded-full bg-gradient-gold mb-5">
                <step.icon className="h-6 w-6 text-primary-foreground" />
              </div>
              <span className="text-xs text-primary font-bold mb-2">
                PASSO {index + 1}
              </span>
              <h3 className="font-heading text-lg font-semibold mb-2 text-foreground">
                {step.title}
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
