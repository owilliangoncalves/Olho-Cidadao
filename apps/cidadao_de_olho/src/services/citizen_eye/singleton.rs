use std::sync::{Arc, OnceLock};

use anyhow::Result;

use super::servico::ServicoCidadaoDeOlho;

static SERVICO: OnceLock<Arc<ServicoCidadaoDeOlho>> = OnceLock::new();

/// Retorna a instância singleton do serviço público do app.
///
/// O backend usa uma instância compartilhada para:
/// - reaproveitar o cache em memória;
/// - evitar recarregar configuração a cada request;
/// - manter um ponto único de orquestração do snapshot.
pub fn servico_compartilhado() -> Result<Arc<ServicoCidadaoDeOlho>> {
    get_or_try_init_arc(&SERVICO, ServicoCidadaoDeOlho::load)
}

fn get_or_try_init_arc<T, F>(cell: &OnceLock<Arc<T>>, loader: F) -> Result<Arc<T>>
where
    F: FnOnce() -> Result<T>,
{
    if let Some(value) = cell.get() {
        return Ok(value.clone());
    }

    let value = Arc::new(loader()?);
    match cell.set(value.clone()) {
        Ok(()) => Ok(value),
        Err(_) => Ok(cell.get().cloned().unwrap_or(value)),
    }
}

#[cfg(test)]
mod tests {
    use std::sync::{
        atomic::{AtomicUsize, Ordering},
        Arc, OnceLock,
    };

    use anyhow::anyhow;

    use super::get_or_try_init_arc;

    #[test]
    fn singleton_inicializa_uma_vez() {
        let cell = OnceLock::new();
        let calls = AtomicUsize::new(0);

        let first = get_or_try_init_arc(&cell, || {
            calls.fetch_add(1, Ordering::SeqCst);
            Ok::<_, anyhow::Error>("snapshot-service".to_string())
        })
        .expect("primeira inicializacao deveria funcionar");

        let second = get_or_try_init_arc(&cell, || {
            calls.fetch_add(1, Ordering::SeqCst);
            Ok::<_, anyhow::Error>("outra-instancia".to_string())
        })
        .expect("segunda leitura deveria reutilizar a instancia");

        assert_eq!(calls.load(Ordering::SeqCst), 1);
        assert_eq!(Arc::as_ptr(&first), Arc::as_ptr(&second));
        assert_eq!(first.as_str(), "snapshot-service");
    }

    #[test]
    fn singleton_propagates_loader_error_without_panicking() {
        let cell = OnceLock::<Arc<String>>::new();

        let error = get_or_try_init_arc(&cell, || Err(anyhow!("configuracao ausente")))
            .expect_err("falha de inicializacao deveria retornar erro");

        assert!(error.to_string().contains("configuracao ausente"));
        assert!(cell.get().is_none());
    }
}
