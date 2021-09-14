# Pogmare Bot

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/BonHowi/discordPogmareBot)](https://github.com/BonHowi/discordPogmareBot)
[![Wakatime](https://wakatime.com/badge/github/BonHowi/discordPogmareBot.svg)](https://wakatime.com/projects/discordPogmareBot)
[![GitHub top language](https://img.shields.io/github/languages/top/BonHowi/discordPogmareBot)](https://github.com/BonHowi/discordPogmareBot)
[![Lines of Code](https://tokei.rs/b1/github/BonHowi/discordPogmareBot?category=code)](https://sonarcloud.io/dashboard?id=BonHowi_discordPogmareBot)
[![GitHub repo size](https://img.shields.io/github/repo-size/BonHowi/discordPogmareBot)](https://github.com/BonHowi/discordPogmareBot)
[![Sonar Quality Gate](https://img.shields.io/sonar/quality_gate/BonHowi_discordPogmareBot?server=https%3A%2F%2Fsonarcloud.io)](https://sonarcloud.io/dashboard?id=BonHowi_discordPogmareBot)
[![Code Climate maintainability](https://img.shields.io/codeclimate/maintainability/BonHowi/discordPogmareBot)](https://codeclimate.com/github/BonHowi/discordPogmareBot/maintainability)
[![Scrutinizer code quality (GitHub/Bitbucket)](https://img.shields.io/scrutinizer/quality/g/BonHowi/discordPogmareBot)](https://scrutinizer-ci.com/g/BonHowi/discordPogmareBot/reports/)
[![Discord Shield](https://discordapp.com/api/guilds/871434324023599155/widget.png?style=shield)](https://discord.gg/Kt35Jtc5nT)




## Table of contents
* [General info](#general-info)
* [Setup](#setup)
* [Functions](#functions)


## General info

Pogmare is a Discord bot made for [W:MS Spotters](https://discord.gg/Kt35Jtc5nT) server. Main functionalites are focused on countibg monster spots and displaying leaderboards, but the bot offers a lot of smaller tools for moderators and the community.


## Setup

_Recommended Python3.7.7_

* Create and virtual env
    * `python -m venv c:\path\to\myenv`
* Connect to virtual env
    * Windows: `venv\Scripts\activate`
    * Linux: `source venv\bin\activate`
* Install MySQL
    * Create server_database 
* Install dependencies
    * `pip install -r requirements.txt`
* Create server files in server_files folder
    * bot_settings.json - template .json file in [get_settings.py](https://github.com/BonHowi/discordPogmareBot/blob/main/modules/get_settings.py)
    * config.json - generated in [pull_config.py](https://github.com/BonHowi/discordPogmareBot/blob/main/modules/pull_config/pull_config.py). To use it access to [this google sheet](https://docs.google.com/spreadsheets/d/1tm5l3He3O-KxCYpTtYURtRjz17uhsNFgco_Z4EUbOgM/edit?usp=sharing) is needed. You can create your own sheet or config as well


## Functions

* Counting monster spots
* Displaying leaderboards
* Requesting roles
* Updating config file
* Interacting with server database
* Slash commands
    * _Will be listed soon™_


