import { Car } from "lucide-react";

const Footer = () => {
  return (
    <footer className="border-t border-border bg-card py-12">
      <div className="container">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <Car className="h-5 w-5 text-primary" />
            <span className="font-heading text-lg font-bold text-gradient-gold">Placa Preta</span>
          </div>
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} Placa Preta — Avaliação de Veículos Antigos. Todos os direitos reservados.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
