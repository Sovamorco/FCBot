from vk_botting import Cog
from pydot import Dot, Edge, Subgraph, Node

from cogs.general import *


class Profiles(Cog):

    @command(name='ник', aliases=['поменять ник', 'поменять ник на'], usage='ник <ник>', help='Команда для смены ника')
    async def set_nickname(self, ctx, *, nickname=''):
        if len(nickname) > 25 or len(nickname) < 1:
            return await ctx.send(answers['warnings']['bad_nickname_size'])
        if any(ch in nickname for ch in ['|', '\n', ']', '[', '$']) or nickname.endswith((':', '-')):
            return await ctx.send(answers['warnings']['bad_nickname_symbols'])
        if re.search(all_regex, nickname.lower()):
            return await ctx.send(answers['warnings']['no'])
        prof = await FCMember.load(ctx.from_id)
        prof.nick = nickname
        await ctx.send(answers['confirmations']['general'])
        return await prof.dump()

    @command(name='профиль', usage='профиль [id]',
             help='Команда для просмотра своего профиля или профиля другого пользователя')
    async def profile(self, ctx, uid=None):
        uid = await IDConverter(True).convert(ctx, uid)
        prof = await FCMember.load(uid)
        lines = [answers['profiles']['profile']['header'].format(await prof.get_mention()),
                 answers['profiles']['profile']['warnings'].format(await prof.get_warnings_count(ctx.peer_id))]
        roles = await prof.get_roles()
        lines += [answers['profiles']['profile']['role'].format(role.name.capitalize()) for role in roles] or \
                 [answers['profiles']['profile']['role'].format('Участник')]
        invited = await get_invite(uid)
        lines += [answers['profiles']['profile']['cookies'].format(prof.cookies),
                  answers['profiles']['profile']['invited'].format(invited.strftime('%d.%m.%Y')),
                  '', answers['profiles']['profile']['disclaimer']]
        return await ctx.send('\n'.join(lines))

    @command(name='подарить печеньки', usage='подарить печеньки <id> <кол-во>',
             aliases=['перевести', 'перевести печеньки', 'подарить', 'поделиться', 'поделиться печеньками'],
             help='Эта команда позволяет делиться печеньками с другими пользователями')
    async def gift_cookies(self, ctx, uid: IDConverter(), amt: int):
        if amt <= 0:
            return await ctx.send(answers['warnings']['bad_posint'])
        prof = await FCMember.load(ctx.from_id)
        if amt > prof.cookies:
            return await ctx.send(answers['warnings']['not_enough_cookies'])
        tprof = await FCMember.load(uid)
        prof.cookies -= amt
        tprof.cookies += amt
        await ctx.send(answers['confirmations']['general'])
        await prof.dump()
        return await tprof.dump()

    @command(name='брак запрос', aliases=['запрос в брак', 'запрос на брак', 'запрос брака', 'запрос'], usage='брак запрос <id>',
             help='Эта команда позволяет отправить пользователю запрос на брак')
    async def proposal(self, ctx, target: IDConverter()):
        prof = await FCMember.load(ctx.from_id)
        tprof = await FCMember.load(target)
        if target == ctx.from_id:
            return await ctx.send(answers['warnings']['proposal']['no_selfcest'])
        family = await prof.get_family()
        if family.partner:
            return await ctx.send(answers['warnings']['proposal']['already_married'])
        if await prof.get_outgoing_request():
            return await ctx.send(answers['warnings']['proposal']['active_outgoing_request'].format(ctx.prefix))
        tfamily = await tprof.get_family()
        if tfamily.partner:
            return await ctx.send(answers['warnings']['proposal']['target_already_married'])
        if await tprof.get_incoming_request():
            return await ctx.send(answers['warnings']['proposal']['active_incoming_request'])
        dz = await family.get_danger_zone()
        if target in dz:
            return await ctx.send(answers['warnings']['proposal']['no_incest'])
        await prof.send_request(target)
        return await ctx.send(answers['confirmations']['general'])

    @command(name='брак принять', aliases=['принять', 'свадьба'], used_art='свадьба', help='Эта команда принимает запрос на брак')
    async def accept(self, ctx):
        prof = await FCMember.load(ctx.from_id)
        if not await prof.get_incoming_request():
            return await ctx.send(answers['warnings']['no_incoming_request'])
        await prof.accept_request()
        ment = await fcbot.get_mention(ctx.from_id)
        sment = await fcbot.get_mention(prof.brak_pair)
        return await ctx.send(answers['confirmations']['wedding'].format(ment, sment), attachment=await fcbot.get_random_art(ctx.command.used_art))

    @command(name='брак отклонить', aliases=['отклонить'], help='Эта команда отклоняет входящий запрос на брак')
    async def decline(self, ctx):
        prof = await FCMember.load(ctx.from_id)
        if not await prof.get_incoming_request():
            return await ctx.send(answers['warnings']['no_incoming_request'])
        await prof.cancel_incoming_request()
        return await ctx.send(answers['confirmations']['general'])

    @command(name='брак отменить', aliases=['отменить'], help='Эта команда отменяет исходящий запрос на брак')
    async def cancel(self, ctx):
        prof = await FCMember.load(ctx.from_id)
        if not await prof.get_outgoing_request():
            return await ctx.send(answers['warnings']['no_outgoing_request'])
        await prof.cancel_outgoing_request()
        return await ctx.send(answers['confirmations']['general'])

    @command(name='брак развод', aliases=['развод'], used_art='развод')
    async def divorce(self, ctx):
        prof = await FCMember.load(ctx.from_id)
        family = await prof.get_family()
        if not family.partner:
            return await ctx.send(answers['warnings']['not_married'])
        await family.divorce()
        ment = await prof.get_mention()
        sment = await fcbot.get_mention(family.partner)
        await ctx.send(answers['confirmations']['divorce'].format(ment, sment),
                       attachment=await fcbot.get_random_art(ctx.command.used_art))

    @command(name='согласен быть ребенком', help='Эта команда позволяет принять запрос на становление ребенком',
             aliases=['стать ребенком', 'стать ребёнком', 'согласен быть ребёнком', 'хочу быть ребенком', 'хочу быть ребёнком',
                      'согласен стать ребенком', 'согласен стать ребёнком'])
    async def become_a_child(self, ctx):
        prof = await FCMember.load(ctx.from_id)
        family = await prof.get_family()
        if await family.get_parents():
            return await ctx.send(answers['warnings']['child']['already_have_parents'])
        pot = await family.get_parents(True)
        if not pot:
            return await ctx.send(answers['warnings']['child']['no_request'])
        pfamily = await pot[0].get_family()
        psiblings = await pfamily.get_children()
        if len(psiblings) >= child_limit:
            return await ctx.send(answers['warnings']['child']['too_many_children'])
        await prof.accept_child_request()
        return await ctx.send(answers['confirmations']['general'])

    @command(name='не хочу быть', help='Эта команда позволяет отклонить запрос на страновление ребенком',
             aliases=['не хочу быть ребенком', 'не хочу быть ребёнком', 'отказаться быть ребенком', 'отказаться быть ребёнком',
                      'не становиться ребенком', 'не становиться ребёнком'])
    async def not_become_a_child(self, ctx):
        prof = await FCMember.load(ctx.from_id)
        family = await prof.get_family()
        if await family.get_parents():
            return await ctx.send(answers['warnings']['child']['already_have_parents'])
        if not await family.get_parents(True):
            return await ctx.send(answers['warnings']['child']['no_request'])
        await prof.leave_parents()
        return await ctx.send(answers['confirmations']['general'])

    @command(name='сбежать от родаков', aliases=['сбежать от родителей', 'уйти от родителей', 'убежать от родителей'],
             help='Эта команда позволяет ребенку покинуть семью')
    async def leave_parents(self, ctx):
        prof = await FCMember.load(ctx.from_id)
        family = await prof.get_family()
        if not await family.get_parents():
            return await ctx.send(answers['warnings']['child']['no_parents'])
        await prof.leave_parents()
        return await ctx.send(answers['confirmations']['general'])

    @command(name='сдать в детдом', aliases=['сдать'], usage='сдать в детдом <ид>',
             help='Эта команда позволяет отправить одного из своих детей в детдом')
    async def drop_a_child(self, ctx, target: IDConverter()):
        prof = await FCMember.load(ctx.from_id)
        family = await prof.get_family()
        if not family.partner:
            return await ctx.send(answers['warnings']['not_married'])
        children = await family.get_children()
        if not any(child.id == target for child in children):
            return await ctx.send(answers['warnings']['not_your_child'])
        uprof = await FCMember.load(target)
        await uprof.leave_parents()
        await ctx.send(answers['confirmations']['general'])

    @command(name='завести ребенка', aliases=['+ребенок', 'завести ребёнка'], help='Команда, позволяющая завести ребенка, если вы в браке',
             usage='завести ребенка <ид>')
    async def make_a_child(self, ctx, target: IDConverter()):
        prof = await FCMember.load(ctx.from_id)
        family = await prof.get_family()
        if not family.partner:
            return await ctx.send(answers['warnings']['not_married'])
        children = await family.get_children()
        if len(children) >= child_limit:
            return await ctx.send(answers['warnings']['too_many_children'])
        tprof = await FCMember.load(target)
        tfamily = await tprof.get_family()
        if await tfamily.get_parents():
            return await ctx.send(answers['warnings']['already_has_parents'])
        if await tfamily.get_parents(True):
            return await ctx.send(answers['warnings']['already_requested'].format(ctx.prefix))
        dz = await family.get_danger_zone()
        if target in dz:
            return await ctx.send(answers['warnings']['dangerous_child'])
        await family.add_child(target)
        return await ctx.send(answers['confirmations']['child_requested'].format(ctx.prefix))

    @command(name='семья', usage='семья [id]', help='Команда для просмотра своей семьи или семьи другого пользователя')
    async def family(self, ctx, uid=None):
        uid = await IDConverter(True).convert(ctx, uid)
        prof = await FCMember.load(uid)
        family = await prof.get_family()
        parents = await family.get_parents()
        lines = [answers['profiles']['family']['header'].format(await prof.get_mention()), '']
        if not parents:
            lines.append(answers['profiles']['family']['parents'][0])
        else:
            lines.append(answers['profiles']['family']['parents'][1].format(*[await parent.get_mention() for parent in parents]))
            lines.append('')
            siblings = await family.get_siblings()
            if not siblings:
                lines.append(answers['profiles']['family']['siblings'][0])
            else:
                for sibling in siblings:
                    gender = await fcbot.get_gender_end(sibling.id)
                    lines.append(answers['profiles']['family']['siblings'][1 if gender else 2].format(await sibling.get_mention()))
        lines.append('')
        if not family.partner:
            lines.append(answers['profiles']['family']['partner'][0])
            lines.append('')
            lines.append(answers['profiles']['family']['children'][0])
        else:
            lines.append(answers['profiles']['family']['partner'][1].format(await fcbot.get_mention(family.partner)))
            lines.append('')
            children = await family.get_children()
            if not children:
                lines.append(answers['profiles']['family']['children'][0])
            else:
                for child in children:
                    gender = await fcbot.get_gender_end(child.id)
                    lines.append(answers['profiles']['family']['children'][1 if gender else 2].format(await child.get_mention()))
        return await ctx.send('\n'.join(lines))

    @command(name='семейное древо', aliases=['древо'], usage='семейное древо [id]', help='Команда для генерации семейного древа пользователя')
    async def family_tree(self, ctx, uid=None):
        uid = await IDConverter(True).convert(ctx, uid)
        indis = {}
        fams = {}

        async def get_name_and_gender(iuid):
            if iuid in users_cache:
                return users_cache[iuid].first_name + ' ' + users_cache[iuid].last_name, users_cache[iuid].sex
            iuser = await fcbot.get_user(iuid, fields='sex')
            users_cache[iuid] = iuser
            return iuser.first_name + ' ' + iuser.last_name, iuser.sex

        async def parse_one(prof):
            if prof.id in indis:
                return
            name, gen = await get_name_and_gender(prof.id)
            indis[prof.id] = [name, gen, False]
            family = await prof.get_family()
            return await parse_family(family)

        async def parse_family(family: Family):
            fid = f'family{family.id}'
            if fid in fams:
                return
            if family.partner:
                fams[fid] = {
                    'parents': [family.self, family.partner],
                    'children': []
                }
                await parse_one(await family.get_partner())
            children = await family.get_children()
            for ichild in children:
                await parse_one(ichild)
                indis[ichild.id][2] = True
                fams[fid]['children'].append(ichild.id)
            parents = await family.get_parents()
            if parents:
                for parent in parents:
                    await parse_one(parent)

        uprof = await FCMember.load(uid)
        await parse_one(uprof)

        m = Dot(bgcolor='white', center='true', charset='utf8', concentrate='false', dpi=160, margin='"0.39,0.39"', mclimit=99, nodesep=0.3, outputorder='edgesfirst',
                pagedir='BL', rankdir='TB', ranksep=0.3, ratio='fill', searchsize=100, size='"25,15"', splines='true')
        m.set_graph_defaults(fontsize=25)
        m.set_edge_defaults(len=0.5, style='solid', fontsize=25)
        m.set_node_defaults(style='filled', fontname='Helvetica', fontsize=25)
        for indi in indis:
            nm = "\\n".join(indis[indi][0].split(' ', 1))
            if indi == uid:
                new = Node(name=indi, shape="box", fillcolor="#ff003f", style='"solid,filled"' if indis[indi][1] == 2 else '"rounded,filled"', label=nm, fontsize=25)
            elif indis[indi][1] == 2:
                new = Node(name=indi, shape="box", fillcolor="#e0e0ff", style='"solid,filled"', label=nm, fontsize=25)
            else:
                new = Node(name=indi, shape="box", fillcolor="#ffe0e0", style='"rounded,filled"', label=nm, fontsize=25)
            m.add_node(new)
        for fam in fams:
            new = Node(name=fam, shape="ellipse", fillcolor="#ffffe0", style="filled", label="")
            m.add_node(new)
            sub = Subgraph(graph_name=f'cluster_{fam}', style='invis')
            if indis[fams[fam]['parents'][0]][2]:
                e = Edge(fams[fam]["parents"][0], fams[fam]["parents"][1], style='invis', arrowhead='none', arrowtail='none', dir='both')
            else:
                e = Edge(fams[fam]["parents"][1], fams[fam]["parents"][0], style='invis', arrowhead='none', arrowtail='none', dir='both')
            sub.add_edge(e)
            me = Edge(fams[fam]["parents"][0], fam, arrowhead='normal', arrowtail='none', dir='both')
            sub.add_edge(me)
            fe = Edge(fams[fam]["parents"][1], fam, arrowhead='normal', arrowtail='none', dir='both')
            sub.add_edge(fe)
            m.add_subgraph(sub)
            for child in fams[fam]['children']:
                e = Edge(fam, child, style='solid', arrowhead='normal', arrowtail='none', dir='both')
                m.add_edge(e)

        res = await fcbot.upload_photo(ctx.peer_id, raw=m.create_png(encoding='utf-8'), format='png')
        return await ctx.send(attachment=res)

    @command(name='статус -', aliases=['оценить -', 'дизлайк', 'понизить', 'минус'], usage='статус - <id> [комментарий]',
             help='Команда для понижения статуса пользователя')
    async def decrease_standing(self, ctx, target: IDConverter(), *, comment=''):
        pass

    @command(name='статус +', aliases=['оценить +', 'лайк', 'повысить', 'плюс'], usage='статус + <id> [комментарий]',
             help='Команда для повышения статуса пользователя')
    async def increase_standing(self, ctx, target: IDConverter(), *, comment=''):
        pass


def profiles_setup():
    fcbot.add_cog(Profiles())
