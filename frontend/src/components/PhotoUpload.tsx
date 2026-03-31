import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Camera, X, Upload, ArrowLeft, ArrowRight, Check } from "lucide-react";

const photoTypes = [
  { id: "frente", label: "Frente do veículo", required: true },
  { id: "traseira", label: "Traseira", required: true },
  { id: "lateral_direita", label: "Lateral direita", required: true },
  { id: "lateral_esquerda", label: "Lateral esquerda", required: true },
  { id: "interior", label: "Interior", required: true },
  { id: "painel", label: "Painel", required: true },
  { id: "motor", label: "Motor", required: true },
  { id: "porta_malas", label: "Porta-malas", required: true },
  { id: "chassi", label: "Chassi", required: true },
  { id: "adicional", label: "Foto adicional", required: false },
];

export interface PhotoData {
  [key: string]: File | null;
}

interface PhotoUploadProps {
  onSubmit: (photos: PhotoData) => void;
  onBack: () => void;
}

const PhotoUpload = ({ onSubmit, onBack }: PhotoUploadProps) => {
  const [photos, setPhotos] = useState<PhotoData>({});
  const [previews, setPreviews] = useState<Record<string, string>>({});
  const inputRefs = useRef<Record<string, HTMLInputElement | null>>({});

  const handleFileChange = (id: string, file: File | null) => {
    setPhotos(prev => ({ ...prev, [id]: file }));
    if (file) {
      const url = URL.createObjectURL(file);
      setPreviews(prev => ({ ...prev, [id]: url }));
    } else {
      setPreviews(prev => {
        const newPreviews = { ...prev };
        if (newPreviews[id]) URL.revokeObjectURL(newPreviews[id]);
        delete newPreviews[id];
        return newPreviews;
      });
    }
  };

  const removePhoto = (id: string) => {
    handleFileChange(id, null);
    setPhotos(prev => {
      const n = { ...prev };
      delete n[id];
      return n;
    });
  };

  const requiredCount = photoTypes.filter(p => p.required).length;
  const uploadedRequired = photoTypes.filter(p => p.required && photos[p.id]).length;
  const allRequiredUploaded = uploadedRequired === requiredCount;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center gap-2 mb-2">
        <Camera className="h-5 w-5 text-primary" />
        <h3 className="font-heading text-xl font-semibold">Fotos do Veículo</h3>
      </div>
      <p className="text-sm text-muted-foreground mb-8">
        Envie fotos nítidas e bem iluminadas. Campos com * são obrigatórios.
        ({uploadedRequired}/{requiredCount} obrigatórias enviadas)
      </p>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
        {photoTypes.map(({ id, label, required }) => (
          <div key={id} className="group">
            <div
              onClick={() => inputRefs.current[id]?.click()}
              className={`relative aspect-square rounded-xl border-2 border-dashed cursor-pointer transition-all duration-300 overflow-hidden
                ${photos[id]
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:border-primary/50 bg-surface hover:bg-surface-hover'
                }`}
            >
              {previews[id] ? (
                <>
                  <img src={previews[id]} alt={label} className="w-full h-full object-cover" />
                  <div className="absolute inset-0 bg-background/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <button
                      onClick={e => { e.stopPropagation(); removePhoto(id); }}
                      className="bg-destructive text-destructive-foreground rounded-full p-1.5"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="absolute top-1 right-1 bg-primary rounded-full p-0.5">
                    <Check className="h-3 w-3 text-primary-foreground" />
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center h-full p-2">
                  <Upload className="h-6 w-6 text-muted-foreground mb-1" />
                  <span className="text-[10px] text-muted-foreground text-center leading-tight">{label}</span>
                </div>
              )}
              <input
                ref={el => { inputRefs.current[id] = el; }}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={e => handleFileChange(id, e.target.files?.[0] || null)}
              />
            </div>
            <p className="text-[10px] text-muted-foreground mt-1 text-center truncate">
              {label} {required && <span className="text-primary">*</span>}
            </p>
          </div>
        ))}
      </div>

      <div className="flex justify-between pt-4 border-t border-border">
        <Button variant="goldOutline" onClick={onBack}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Voltar
        </Button>
        <Button variant="gold" onClick={() => onSubmit(photos)} disabled={!allRequiredUploaded}>
          Prosseguir para Pagamento <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};

export default PhotoUpload;
