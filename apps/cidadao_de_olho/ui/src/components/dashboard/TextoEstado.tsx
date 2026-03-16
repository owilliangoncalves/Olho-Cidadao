import type { TextoEstadoProps } from "../../types";

/** Linha textual com reserva visual para quando a interface ainda nao carregou. */
export function TextoEstado({
  texto,
  titulo = false,
  className,
  reservaClassName,
}: TextoEstadoProps) {
  if (!texto) {
    return <div aria-hidden="true" className={reservaClassName} />;
  }

  if (titulo) {
    return <h1 className={className}>{texto}</h1>;
  }

  return <p className={className}>{texto}</p>;
}
