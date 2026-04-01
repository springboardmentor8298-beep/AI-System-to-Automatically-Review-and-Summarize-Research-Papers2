def compare_papers(papers):
    report = "\n📊 CROSS-PAPER COMPARISON REPORT\n\n"

    for paper in papers:
        report += f"📄 {paper['title']}\n"
        report += f"- Findings: {paper['Key_Findings']}\n\n"

    report += "🔍 Conclusion:\n"
    report += "Most papers focus on improving performance and accuracy in their respective domains.\n"

    return report