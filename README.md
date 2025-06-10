> [!IMPORTANT]
> このForkは、現在メンテナンスされていない[Wavelink](https://github.com/PythonistaGuild/Wavelink)を私なりに修正、機能の追加を行うためのものです。  
> 以下のReadmeの翻訳はAIが行っています。Pull requestはお気軽にどうぞ。

> [!WARNING]
> 継続的なアップデートを保証するものではありませんので、その点はご注意ください。  

<div align="center">


![ロゴ](https://raw.githubusercontent.com/PythonistaGuild/Wavelink/master/logo.png)

![Pythonバージョン](https://img.shields.io/pypi/pyversions/Wavelink)
[![PyPI - バージョン](https://img.shields.io/pypi/v/Wavelink)](https://pypi.org/project/wavelink/)
[![Github ライセンス](https://img.shields.io/github/license/PythonistaGuild/Wavelink)](LICENSE)
[![Lavalink バージョン](https://img.shields.io/badge/Lavalink-v4.0%2B-blue?color=%23FB7713)](https://lavalink.dev)
![Lavalink プラグイン](https://img.shields.io/badge/Lavalink_Plugins-Native_Support-blue?color=%2373D673)


</div>


Wavelinkは[Discord.py](https://github.com/Rapptz/discord.py)向けの堅牢で強力なLavalinkラッパーです。
Wavelinkは直感的で使いやすい完全非同期APIを備えています。


### 特徴

- 完全非同期設計。
- REST API対応のLavalink v4+サポート。
- discord.py v2.0.0+サポート。
- 連続再生のための高度な自動再生とトラック推薦。
- 状態を持つオブジェクト指向設計。
- 完全な型アノテーションとPyright strict typing準拠。


## はじめに

**Lavalink:** [GitHub](https://github.com/lavalink-devs/Lavalink/releases), [Webページ](https://lavalink.dev)


## ドキュメント

[公式ドキュメント](https://wavelink.dev/en/latest)


## Lavalink

Wavelink **3**は**Lavalink v4**が必要です。
参照: [Lavalink](https://github.com/lavalink-devs/Lavalink/releases)

Spotifyサポートには、[LavaSrc](https://github.com/topi314/LavaSrc)をインストールし、`wavelink.Playable`で使用してください。


### 注意事項

- Wavelink 3 は Lavalink v4以降 と互換性があります。
- WavelinkはLavaSrcやSponsorBlockなどのLavalinkプラグインをネイティブサポートしています。
- WavelinkはPyright Strictに準拠した完全な型付けがされていますが、discord.pyとwavelink間でいくつかの違いがあります。
