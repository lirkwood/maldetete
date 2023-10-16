use russh::{
    server::{run, Auth, Config, Handler, Msg, Server, Session},
    ChannelId, Preferred,
};
use russh::{Channel, MethodSet};
use russh_keys::key::{self, KeyPair, PublicKey};
use std::{
    collections::HashMap,
    fs::File,
    path::PathBuf,
    sync::{Arc, Mutex},
};

use async_trait::async_trait;

#[tokio::main]
async fn main() {
    let services = systemctl::list_enabled_services().unwrap();
    if services.contains(&"ssh".to_string()) {
        systemctl::stop("ssh").unwrap();
    }

    let mut config = Config::default();
    config.preferred = Preferred {
        key: &[key::ED25519],
        ..Default::default()
    };

    let config = Arc::new(config);

    let server = SSHServer {
        client_pubkey: None,
        clients: Arc::new(Mutex::new(HashMap::new())),
        id: 0,
    };

    tokio::spawn(run(config, ("127.0.0.1", 2222), server))
        .await
        .unwrap()
        .unwrap();
}

#[derive(Clone)]
struct SSHServer {
    client_pubkey: Option<PublicKey>,
    clients: Arc<Mutex<HashMap<(usize, ChannelId), Channel<Msg>>>>,
    id: usize,
}

impl Server for SSHServer {
    type Handler = Self;
    fn new_client(&mut self, _: Option<std::net::SocketAddr>) -> Self {
        let s = self.clone();
        self.id += 1;
        println!("New client number {}", self.id);
        s
    }
}

#[async_trait]
impl Handler for SSHServer {
    type Error = anyhow::Error;

    async fn channel_open_session(
        self,
        channel: Channel<Msg>,
        session: Session,
    ) -> Result<(Self, bool, Session), Self::Error> {
        {
            let mut clients = self.clients.lock().unwrap();
            clients.insert((self.id, channel.id()), channel);
            println!("Session opened");
        }
        Ok((self, true, session))
    }

    async fn auth_publickey(
        mut self,
        _: &str,
        pubkey: &PublicKey,
    ) -> Result<(Self, Auth), Self::Error> {
        self.client_pubkey = Some(pubkey.clone());
        println!("Found pubkey {:?}", pubkey);
        Ok((self, Auth::Accept))
    }

    async fn data(
        self,
        channel: ChannelId,
        data: &[u8],
        mut session: Session,
    ) -> Result<(Self, Session), Self::Error> {
        {
            let mut clients = self.clients.lock().unwrap();
            for ((id, _channel_id), ref mut channel) in clients.iter_mut() {
                channel.data(data);
            }
        }
        Ok((self, session))
    }
}
/// Finds files in a path that pass check_fn
fn find_files(start: PathBuf, check_fn: fn(File) -> bool) {}

fn fake_server() {}
