from langbot_plugin.api.definition.component import Command
from langbot_plugin.api.entities.builtin.pipeline import context
from langbot_plugin.api.entities.builtin.platform import message as platform_message


class AnnounceCommand(Command):

    async def initialize(self):
        pass

    async def execute(self, event_context: context.EventContext, args: list):
        event = event_context.event
        sender_id = str(event.sender_id)

        if not self.plugin.is_admin(sender_id):
            await event_context.reply(
                platform_message.MessageChain(
                    [platform_message.Plain(text="⛔ 你没有权限执行此操作。")]
                )
            )
            return

        if not args:
            await event_context.reply(
                platform_message.MessageChain(
                    [platform_message.Plain(text="用法: !announce <公告内容>")]
                )
            )
            return

        content = " ".join(args)

        try:
            await event_context.call_platform_api(
                "_send_group_notice",
                group_id=event.launcher_id,
                content=content,
            )
            await event_context.reply(
                platform_message.MessageChain(
                    [platform_message.Plain(text=f"📢 群公告已发布。")]
                )
            )
        except Exception as e:
            await event_context.reply(
                platform_message.MessageChain(
                    [platform_message.Plain(text=f"❌ 发布公告失败: {e}")]
                )
            )
