> [!IMPORTANT]
> ~~このForkは、現在メンテナンスされていないWavelinkを私なりに修正、機能の追加を行うためのものです。~~
>   
> 2026/4/11に、[Wavelink](https://github.com/PythonistaGuild/Wavelink)のメンテナンスが再開されました！  
> そのため、こちらのリポジトリはLavalink V5がリリースされるタイミングでアーカイブされます。  

<div align="center">


![ロゴ](https://raw.githubusercontent.com/PythonistaGuild/Wavelink/master/logo.png)

[![Github License](https://img.shields.io/github/license/PythonistaGuild/Wavelink)](LICENSE)
[![Lavalink Version](https://img.shields.io/badge/Lavalink-v4.2%2B-blue?color=%23FB7713)](https://lavalink.dev)
[![NodeLink Version](https://img.shields.io/badge/NodeLink-v3-blue?color=%2344A26B)](https://nodelink.js.org)
![Lavalink Plugin](https://img.shields.io/badge/Lavalink_Plugins-Native_Support-blue?color=%2373D673)


</div>


Wavelinkは、[Discord.py](https://github.com/Rapptz/discord.py)に対応した[Lavalink](https://lavalink.dev)のAPIラッパーです。  


### 特徴

- 非同期で動作
- Lavalink v4.2.0+サポート
- NodeLink v3サポート
- discord.py v2.0.0+サポート
- 24/7連続再生のための高度な自動再生
- Pyright(strict) typingに準拠する型付け

### Lavalink

Wavelinkは**Lavalink v4.2.0以上**が必要です。  
Spotifyを再生するには、Lavalinkに[LavaSrc](https://github.com/topi314/LavaSrc)をインストールし、`wavelink.Playable`で使用できます。

### NodeLink

NodeLinkはLavalinkと同じ方法で接続できます。接続後は `Node.is_nodelink` で判別できます。

### 注意事項

- WavelinkはLavalink v4.2.0+とNodeLink v3に対応しています。
- WavelinkはLavaSrcやSponsorBlockなどのLavalinkプラグインをサポートしています。
- Wavelinkは完全な型付けがされていますが、discord.pyとwavelink間で細かな違いが存在します。
