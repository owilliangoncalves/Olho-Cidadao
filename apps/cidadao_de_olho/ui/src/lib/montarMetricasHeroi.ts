import type { MetricaHeroiModelo, MetricCard } from "../types";

import { metricToneClass } from "./metricToneClass";

/** Prepara as métricas do hero com classes visuais prontas. */
export function montarMetricasHeroi(
  metricas: MetricCard[],
): MetricaHeroiModelo[] {
  return metricas.map((metrica) => ({
    id: metrica.label,
    label: metrica.label,
    value: metrica.value,
    detail: metrica.detail,
    className: metricToneClass(metrica.tone),
  }));
}
