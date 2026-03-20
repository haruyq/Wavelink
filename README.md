> [!IMPORTANT]
> このForkは、現在メンテナンスされていない[Wavelink](https://github.com/PythonistaGuild/Wavelink)を私なりに修正、機能の追加を行うためのものです。  
> PullRequestやIssueはお気軽にどうぞ。  
> 継続的なアップデートを保証するものではありませんので、その点はご注意ください。  

<div align="center">


![ロゴ](https://raw.githubusercontent.com/PythonistaGuild/Wavelink/master/logo.png)

[![Github License](https://img.shields.io/github/license/PythonistaGuild/Wavelink)](LICENSE)
[![Lavalink Version](https://img.shields.io/badge/Lavalink-v4.2%2B-blue?color=%23FB7713)](https://lavalink.dev)
![Lavalink Plugin](https://img.shields.io/badge/Lavalink_Plugins-Native_Support-blue?color=%2373D673)


</div>


Wavelinkは、[Discord.py](https://github.com/Rapptz/discord.py)に対応した[Lavalink](https://lavalink.dev)のAPIラッパーです。  


### 特徴

- 非同期で動作
- Lavalink v4.2.0+サポート
- discord.py v2.0.0+サポート
- 24/7連続再生のための高度な自動再生
- Pyright(strict) typingに準拠する型付け

### Lavalink

Wavelinkは**Lavalink v4.2.0以上**が必要です。  
Spotifyを再生するには、Lavalinkに[LavaSrc](https://github.com/topi314/LavaSrc)をインストールし、`wavelink.Playable`で使用できます。

### 注意事項

- WavelinkはLavalink v4.2.0+に対応しています。それ以外の動作は保証しません。
- WavelinkはLavaSrcやSponsorBlockなどのLavalinkプラグインをサポートしています。
- Wavelinkは完全な型付けがされていますが、discord.pyとwavelink間で細かな違いが存在します。
