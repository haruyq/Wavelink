> [!IMPORTANT]
> このForkは、現在メンテナンスされていない[Wavelink](https://github.com/PythonistaGuild/Wavelink)を私なりに修正、機能の追加を行うためのものです。  
> PullRequestやIssueはお気軽にどうぞ。  
> 継続的なアップデートを保証するものではありませんので、その点はご注意ください。  

<div align="center">


![ロゴ](https://raw.githubusercontent.com/PythonistaGuild/Wavelink/master/logo.png)

[![Github License](https://img.shields.io/github/license/PythonistaGuild/Wavelink)](LICENSE)
[![Lavalink Version](https://img.shields.io/badge/Lavalink-v4.0%2B-blue?color=%23FB7713)](https://lavalink.dev)
![Lavalink Plugin](https://img.shields.io/badge/Lavalink_Plugins-Native_Support-blue?color=%2373D673)


</div>


Wavelinkは[Discord.py](https://github.com/Rapptz/discord.py)に対応したLavalink向けモジュールです。  
Wavelinkは直感的で使いやすい完全非同期APIを備えています。

**Lavalink:** [GitHub](https://github.com/lavalink-devs/Lavalink/releases), [Webページ](https://lavalink.dev)


### 特徴

- 完全に非同期で動作
- Lavalink v4+サポート
- discord.py v2.0.0+サポート
- 連続再生のための高度な自動再生
- 完全な型アノテーションとPyright strict typing準拠

## Lavalink

Wavelink**3**は**Lavalink v4**が必要です。
参照: [Lavalink](https://github.com/lavalink-devs/Lavalink/releases)

Spotifyを再生するには、Lavalinkサーバーに[LavaSrc](https://github.com/topi314/LavaSrc)をインストールし、`wavelink.Playable`で使用できます。


### 注意事項

- Wavelink3はLavalink v4に対応しています。それ以外の動作は保証しません。
- WavelinkはLavaSrcやSponsorBlockなどのLavalinkプラグインをサポートしています。
- WavelinkはPyright Strictに準拠した完全な型付けがされていますが、discord.pyとwavelink間で違いがあります。
