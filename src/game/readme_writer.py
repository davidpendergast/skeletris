import os
import re


def _parse_leading_num(str_with_num):
    just_the_num = re.search(r"\d+", str_with_num).group()
    if just_the_num == "":
        return 0
    else:
        return int(just_the_num)


def write_readme(game_name, template_file, dest_file, gif_directory):
    try:
        with open(template_file, "r") as f:
            template_lines = f.readlines()

        gif_filenames = [f for f in os.listdir(gif_directory) if os.path.isfile(os.path.join(gif_directory, f))]
        gif_filenames = [f for f in gif_filenames if f.endswith(".gif") and f[0].isdigit()]
        gif_filenames.sort(key=_parse_leading_num)
        gif_filenames.reverse()

        result_lines = []
        for line in template_lines:
            name_idx = line.find("{game_name}")
            if name_idx >= 0:
                line = line.replace("{game_name}", game_name)

            found_replacement = False
            for i in range(0, 50):
                if i >= len(gif_filenames):
                    # skip this line, we don't have enough gifs
                    found_replacement = True
                    break
                f_idx = line.find("{file_" + str(i) + "}")
                n_idx = line.find("{name_" + str(i) + "}")
                if f_idx >= 0 and n_idx >= 0:
                    gif_f = gif_filenames[i]
                    gif_n = gif_filenames[i][:-4]  # slice off the ".gif"
                    res_line = line.replace("{file_" + str(i) + "}", gif_f)
                    res_line = res_line.replace("{file_" + str(i) + "}", gif_f)
                    res_line = res_line.replace("{name_" + str(i) + "}", gif_n)
                    found_replacement = True
                    result_lines.append(res_line)
                    break

            if not found_replacement:
                result_lines.append(line)

        with open(dest_file, "w") as dest_f:
            dest_f.write("".join(result_lines))

    except Exception as e:
        print("ERROR: failed to generate readme: {}".format(e))


if __name__ == "__main__":
    write_readme("Skeletris", "readme_template.txt", "README.md", "gifs")
