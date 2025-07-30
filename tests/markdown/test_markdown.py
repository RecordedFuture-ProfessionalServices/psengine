import pytest

from psengine.markdown import MarkdownMaker


class Test_MarkdownMaker:
    sections = [
        (
            'Section 1',
            [
                'Talis cultellus tergiversatio universe. Cruentus demergo admoveo aegre uredo vereor abstergo virga audio arceo. Accusator officia cogito tandem vado adhaero traho eaque casso.',
                'Brevis vestigium suffoco commodo similique. Temperantia tutamen celer. Alius tutis placeat comedo coaegresco cunabula cado minus adulescens cilicium.',
                'Curto complectus verbum aspicio veniam quaerat. Absque dignissimos bibo aufero sint allatus summa. Maiores vacuus videlicet solum deprecator molestiae coniecto.',
                'Commodi desparatus demum caelestis demitto astrum atrox. Velit campana creptio quas similique vehemens viduo ipsa ter anser. Via succedo minus aliquam ubi fugit.',
                'Verto ventosus aut vulgus conitor abscido comparo. Constans vergo advenio calco combibo velum solitudo vesco ustulo cimentarius. Patior texo textus suscipio omnis culpo tondeo.',
            ],
        ),
        (
            'Section 2',
            [
                'Creber umquam quibusdam calcar thalassinus doloremque. Decerno vereor annus amiculum expedita quis. Conturbo adulescens cura aestas verbum demitto sumptus.',
                'Eum trans labore ambitus circumvenio timidus audax vado denuo averto. Triumphus articulus carus carmen volaticus acervus tres necessitatibus aperiam. Aveho comis pauci odio demergo cotidie.',
                'Cupiditate timidus suffoco verumtamen tempus centum. Voro porro decens quos sperno clibanus vere beneficium excepturi constans. Corpus strues admoneo velit deserunt charisma undique coaegresco altus.',
                'Ambitus suppellex quas terreo villa canis. Quaerat aro verto caveo amaritudo teneo. Sono theca decet valde tyrannus concedo umbra tabella.',
                'Alienus defero ullus votum. Cursus dens aro crastinus tenax. Alter vetus vapulus temptatio collum caelestis capio saepe trucido.',
            ],
        ),
    ]

    def test_markdown_maker(self):
        mm = MarkdownMaker()
        mm.add_title('Test Title')
        for title, content in self.sections:
            mm.add_section(title, content)
        markdown = mm.format_output()
        assert markdown.startswith('## Test Title\n\n')
        assert '### Section 1\n\n' in markdown
        assert '### Section 2\n\n' in markdown
        assert markdown.endswith(
            'Alienus defero ullus votum. Cursus dens aro crastinus tenax. Alter vetus vapulus temptatio collum caelestis capio saepe trucido.\n\n'
        )

    # Length of test markdown is 1687 characters
    @pytest.mark.parametrize('character_limit', [200, 500, 1000, 1687])
    def test_char_limit_lte_md_length(self, character_limit):
        mm = MarkdownMaker(addendum='Test Addendum', character_limit=character_limit)
        mm.add_title('Test Title')
        for title, content in self.sections:
            mm.add_section(title, content)
        markdown = mm.format_output()
        assert len(markdown) == character_limit

    # Length of test markdown is 1687 characters
    @pytest.mark.parametrize('character_limit', [1688, 2000])
    def test_char_limit_gt_md_length(self, character_limit):
        mm = MarkdownMaker(addendum='Test Addendum', character_limit=character_limit)
        mm.add_title('Test Title')
        for title, content in self.sections:
            mm.add_section(title, content)
        markdown = mm.format_output()
        assert len(markdown) == 1687

    @pytest.mark.parametrize('character_limit', [-1, 0, 5, 10, 12])
    def test_char_limit_too_low_raises_ValueError(self, character_limit):
        with pytest.raises(ValueError):
            MarkdownMaker(addendum='Test Addendum', character_limit=character_limit)
