import { Check, Star } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import carEngine from "@/assets/car-engine.jpg";

const features = [
  "Análise de originalidade do veículo",
  "Avaliação do estado da pintura",
  "Avaliação do interior e estofamento",
  "Análise da mecânica aparente",
  "Pontuação de 0 a 100 pontos",
  "Relatório técnico em PDF",
  "Envio automático por email",
  "Padrão FBVA de avaliação",
];

const PricingSection = () => {
  return (
    <section className="relative py-24 overflow-hidden">
      {/* Background image */}
      <div className="absolute inset-0">
        <img
          src={carEngine}
          alt=""
          loading="lazy"
          width={1280}
          height={720}
          className="w-full h-full object-cover opacity-[0.07]"
        />
        <div className="absolute inset-0 bg-background/95" />
      </div>

      <div className="container relative z-10 px-4">
        <div className="text-center mb-16">
          <span className="text-xs uppercase tracking-[0.3em] text-primary font-medium">
            Investimento
          </span>
          <h2 className="font-heading text-3xl md:text-4xl font-bold mt-3">
            Avaliação <span className="text-gradient-gold">Completa</span>
          </h2>
        </div>

        <div className="max-w-md mx-auto">
          <div className="relative rounded-2xl border-2 border-primary bg-card/80 backdrop-blur-sm p-8 glow-gold">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2">
              <div className="flex items-center gap-1 bg-gradient-gold px-4 py-1 rounded-full">
                <Star className="h-3 w-3 text-primary-foreground" />
                <span className="text-xs font-bold text-primary-foreground uppercase tracking-wider">
                  Premium
                </span>
              </div>
            </div>

            <div className="text-center mb-8 mt-4">
              <div className="flex items-baseline justify-center gap-1">
                <span className="text-sm text-muted-foreground">R$</span>
                <span className="font-heading text-5xl font-bold text-gradient-gold">197</span>
                <span className="text-sm text-muted-foreground">,00</span>
              </div>
              <p className="text-sm text-muted-foreground mt-2">Pagamento único</p>
            </div>

            <ul className="space-y-3 mb-8">
              {features.map((feature, index) => (
                <li key={index} className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-5 h-5 rounded-full bg-primary/20">
                    <Check className="h-3 w-3 text-primary" />
                  </div>
                  <span className="text-sm text-secondary-foreground">{feature}</span>
                </li>
              ))}
            </ul>

            <Link to="/avaliacao">
              <Button variant="gold" size="lg" className="w-full text-base py-6">
                Iniciar Avaliação Agora
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PricingSection;
