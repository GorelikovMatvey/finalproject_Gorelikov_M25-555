#!/usr/bin/env python3
"""
Интерактивный CLI — единственная точка входа для пользовательских команд.
"""

import argparse
import shlex
import sys

from ..core import usecases
from ..core.constants import (
    API_ERROR_SUGGESTION,
    AVAILABLE_COMMANDS,
    COMMAND_EXAMPLES,
    COMMAND_HELP_NOT_FOUND,
    COMMAND_HELP_TEXTS,
    COMMAND_USAGE,
    CURRENCY_NOT_FOUND_HELP,
    GOODBYE_MESSAGE,
    HELP_PROMPT,
    INTERNAL_CLI_ERROR,
    UNKNOWN_COMMAND,
    USER_INTERRUPT,
    WELCOME_MESSAGE,
)
from ..core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)


class SilentArgumentParser(argparse.ArgumentParser):
    """ArgumentParser который не выводит сообщения об ошибках."""

    def _print_message(self, message, file=None):
        """Подавляет вывод сообщений."""
        pass

    def exit(self, status=0, message=None):
        """Подавляет выход из программы."""
        raise argparse.ArgumentError(None, message or "")


def show_help():
    """Показывает список доступных команд и примеры использования."""
    print("\n📘 Доступные команды:")
    for cmd, desc in AVAILABLE_COMMANDS.items():
        print(f"  {cmd:<15} — {desc}")
    print("\nПримеры:")
    for example in COMMAND_EXAMPLES:
        print(f"  {example}")
    print("\nВведите команду или 'exit' для выхода.\n")


def parse_cmd_line(line: str):
    """
    Разбирает введённую строку и возвращает (cmd, parsed_args).

    Использует shlex для корректного парсинга строк с кавычками и пробелами.
    При ошибках парсинга возвращает команду помощи для данной команды.
    """
    if not line.strip():
        return None, None

    try:
        # Используем shlex для корректного разбиения строки.
        parts = shlex.split(line.strip())
    except ValueError as e:
        # Ошибка парсинга (например, незакрытые кавычки).
        print(f"❌ Ошибка синтаксиса: {e}")
        return None, None

    if not parts:
        return None, None

    cmd = parts[0]
    rest = parts[1:]

    # Простые команды без аргументов.
    if cmd in ("help", "exit"):
        return cmd, None

    try:
        # Команды с аргументами.
        if cmd == "register":
            parser = SilentArgumentParser(prog="register", add_help=False)
            parser.add_argument("--username", required=True)
            parser.add_argument("--password", required=True)
            return "register", parser.parse_args(rest)

        if cmd == "login":
            parser = SilentArgumentParser(prog="login", add_help=False)
            parser.add_argument("--username", required=True)
            parser.add_argument("--password", required=True)
            return "login", parser.parse_args(rest)

        if cmd == "show-portfolio":
            parser = SilentArgumentParser(
                prog="show-portfolio", add_help=False
            )
            parser.add_argument("--base", default=None)
            return "show-portfolio", parser.parse_args(rest)

        if cmd == "buy":
            parser = SilentArgumentParser(prog="buy", add_help=False)
            parser.add_argument("--currency", required=True)
            parser.add_argument("--amount", type=float, required=True)
            return "buy", parser.parse_args(rest)

        if cmd == "sell":
            parser = SilentArgumentParser(prog="sell", add_help=False)
            parser.add_argument("--currency", required=True)
            parser.add_argument("--amount", type=float, required=True)
            return "sell", parser.parse_args(rest)

        if cmd == "get-rate":
            parser = SilentArgumentParser(prog="get-rate", add_help=False)
            parser.add_argument("--from", dest="from_code", required=True)
            parser.add_argument("--to", dest="to_code", required=True)
            return "get-rate", parser.parse_args(rest)

        if cmd == "update-rates":
            parser = SilentArgumentParser(
                prog="update-rates", add_help=False
            )
            parser.add_argument(
                "--source",
                choices=["coingecko", "exchangerate"],
                default=None
            )
            return "update-rates", parser.parse_args(rest)

        if cmd == "show-rates":
            parser = SilentArgumentParser(prog="show-rates", add_help=False)
            parser.add_argument("--currency", type=str, default=None)
            parser.add_argument("--top", type=int, default=None)
            parser.add_argument("--base", type=str, default=None)
            return "show-rates", parser.parse_args(rest)

        if cmd == "deposit":
            parser = SilentArgumentParser(prog="deposit", add_help=False)
            parser.add_argument("--amount", type=float, required=True)
            return "deposit", parser.parse_args(rest)

        # Неизвестная команда.
        return cmd, None

    except (SystemExit, argparse.ArgumentError, Exception):
        # При любой ошибке парсинга показываем справку по команде.
        return f"help_{cmd}", None


def _show_command_help(command: str):
    """Показывает справку по конкретной команде."""
    if command in COMMAND_HELP_TEXTS:
        print(COMMAND_USAGE.format(COMMAND_HELP_TEXTS[command]))
    else:
        print(COMMAND_HELP_NOT_FOUND.format(command))


def main_cli():
    """Основной цикл интерфейса командной строки."""
    print(WELCOME_MESSAGE)
    print(HELP_PROMPT)

    running = True
    while running:
        try:
            line = input("> ").strip()
            if not line:
                continue

            cmd, args = parse_cmd_line(line)
            if cmd is None:
                continue

            try:
                if cmd == "help":
                    show_help()
                elif cmd == "exit":
                    print(GOODBYE_MESSAGE)
                    running = False
                    continue
                elif cmd.startswith("help_"):
                    # Показываем справку по конкретной команде.
                    actual_cmd = cmd[5:]  # Убираем "help_".
                    _show_command_help(actual_cmd)
                elif cmd == "register":
                    print(usecases.register(args.username, args.password))
                elif cmd == "login":
                    print(usecases.login(args.username, args.password))
                elif cmd == "show-portfolio":
                    base = args.base if args else None
                    print(usecases.show_portfolio(base))
                elif cmd == "buy":
                    print(usecases.buy(args.currency, args.amount))
                elif cmd == "sell":
                    print(usecases.sell(args.currency, args.amount))
                elif cmd == "get-rate":
                    print(usecases.get_rate(args.from_code, args.to_code))
                elif cmd == "update-rates":
                    source = args.source if args else None
                    print(usecases.update_rates(source=source))
                elif cmd == "show-rates":
                    currency = args.currency if args else None
                    top = args.top if args else None
                    base = args.base if args else None
                    print(usecases.show_rates(
                        currency=currency, top=top, base=base
                    ))
                elif cmd == "start-scheduler":
                    from ..parser_service.scheduler import SimpleScheduler
                    scheduler = SimpleScheduler(
                        interval_seconds=60)  # Обновление каждую минуту.
                    scheduler.start()
                    print("✅ Планировщик запущен (интервал: 60 секунд)")
                elif cmd == "deposit":
                    print(usecases.deposit(args.amount))
                else:
                    print(UNKNOWN_COMMAND.format(cmd))

            # Перехват ошибок доменного уровня.
            except InsufficientFundsError as e:
                print(str(e))
            except CurrencyNotFoundError as e:
                print(f"❌ {e}")
                print(CURRENCY_NOT_FOUND_HELP)
            except ApiRequestError as e:
                print(f"{e}\n{API_ERROR_SUGGESTION}")

        except KeyboardInterrupt:
            print(USER_INTERRUPT)
        except Exception as e:
            print(INTERNAL_CLI_ERROR.format(e))

    sys.exit(0)
