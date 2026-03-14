/**
 * Estados de tela usados quando o snapshot ainda não está disponível.
 *
 * Esses componentes existem para manter `App.tsx` focado em composição e
 * evitar espalhar as telas de carregamento e erro pela árvore principal.
 */
import { RefreshCcw } from "lucide-react";

/** Tela exibida enquanto o snapshot público está sendo carregado. */
export function EstadoCarregando() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0a0d15]">
      <div className="rounded-[2rem] border border-white/10 bg-white/5 px-8 py-7 text-center shadow-2xl">
        <p className="text-[11px] uppercase tracking-[0.28em] text-stone-500">
          Carregando
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-white">
          Montando o feed civico
        </h1>
        <p className="mt-3 text-sm text-stone-300">
          Cruzando Camara, Senado e a dimensao publica de fornecedores.
        </p>
      </div>
    </div>
  );
}

/** Tela de erro inicial com ação de nova tentativa. */
export function EstadoErro({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0a0d15] px-4">
      <div className="max-w-lg rounded-[2rem] border border-red-400/20 bg-red-300/8 px-8 py-7 shadow-2xl">
        <p className="text-[11px] uppercase tracking-[0.28em] text-red-200">
          Falha de leitura
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-white">
          O radar público não abriu agora
        </h1>
        <p className="mt-3 text-sm leading-7 text-stone-200">{message}</p>
        <button
          type="button"
          onClick={onRetry}
          className="mt-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-sm text-white transition hover:bg-white/15"
        >
          <RefreshCcw size={16} />
          Tentar novamente
        </button>
      </div>
    </div>
  );
}
