const fs = require('fs');

function htmlToJsx(html) {
    return html
        .replace(/class=/g, 'className=')
        .replace(/<!--/g, '{/*')
        .replace(/-->/g, '*/}')
        .replace(/onclick=/gi, 'onClick=')
        .replace(/stroke-width=/gi, 'strokeWidth=')
        .replace(/stroke-linecap=/gi, 'strokeLinecap=')
        .replace(/stroke-linejoin=/gi, 'strokeLinejoin=')
        .replace(/fill-rule=/gi, 'fillRule=')
        .replace(/clip-rule=/gi, 'clipRule=')
        .replace(/<img(.*?)>/gi, '<img$1 />')
        .replace(/<br>/gi, '<br />')
        .replace(/<input(.*?)>/gi, '<input$1 />')
        // other self-closing tags if necessary
}

const files = ['upload.html', 'results.html', 'profile.html'];
for (const file of files) {
    const path = `../.stitch/designs/${file}`;
    if(fs.existsSync(path)) {
        const content = fs.readFileSync(path, 'utf8');
        const mainMatch = content.match(/<main[\s\S]*?<\/main>/);
        const navMatch = content.match(/<header[\s\S]*?<\/header>/);
        if (mainMatch) {
            fs.writeFileSync(`../.stitch/designs/${file.replace('.html', '.jsx')}`, htmlToJsx(navMatch ? navMatch[0] + '\n' + mainMatch[0] : mainMatch[0]));
        }
    }
}
