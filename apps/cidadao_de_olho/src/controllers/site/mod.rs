//! Entrega da interface web pública.
//!
//! O backend serve o `index.html` gerado pelo frontend e faz fallback para uma
//! página mínima quando o bundle ainda não foi compilado.

mod index;
mod load_index_html;
mod routes;

pub use self::routes::routes;
